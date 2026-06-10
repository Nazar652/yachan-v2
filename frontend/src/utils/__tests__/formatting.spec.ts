import { describe, expect, it } from 'vitest'

import { applyFormat, checkFormat, findCodeRegions, REFUSAL } from '@/utils/formatting'

function applied(text: string, start: number, end: number, format: Parameters<typeof applyFormat>[3]) {
  const outcome = applyFormat(text, start, end, format)
  if (!outcome.applied) throw new Error(`expected application, got refusal: ${outcome.reason}`)
  return outcome
}

function refused(text: string, start: number, end: number, format: Parameters<typeof applyFormat>[3]) {
  const outcome = applyFormat(text, start, end, format)
  if (outcome.applied) throw new Error('expected refusal, got application')
  return outcome
}

describe('findCodeRegions', () => {
  it('finds an inline code span', () => {
    expect(findCodeRegions('a `x` b')).toEqual({ inline: [{ start: 2, end: 5 }], block: [] })
  })

  it('pairs runs of equal backtick length', () => {
    expect(findCodeRegions('a ``x`` b').inline).toEqual([{ start: 2, end: 7 }])
  })

  it('ignores an unmatched backtick', () => {
    expect(findCodeRegions('a ` b').inline).toEqual([])
  })

  it('does not pair across a blank line', () => {
    expect(findCodeRegions('a `x\n\ny` b').inline).toEqual([])
  })

  it('finds a fenced code block', () => {
    expect(findCodeRegions('a\n```\ncode\n```\nb').block).toEqual([{ start: 2, end: 14 }])
  })

  it('extends an unclosed fence to the end of text', () => {
    expect(findCodeRegions('```\ncode').block).toEqual([{ start: 0, end: 8 }])
  })

  it('does not treat backticks inside a fence as inline spans', () => {
    expect(findCodeRegions('```\n`x`\n```').inline).toEqual([])
  })

  it('supports tilde fences', () => {
    expect(findCodeRegions('~~~\nx\n~~~').block).toEqual([{ start: 0, end: 9 }])
  })
})

describe('applyFormat wrapping', () => {
  it('wraps the selection in bold and keeps the inner text selected', () => {
    expect(applied('bold it', 0, 4, 'bold')).toEqual({
      applied: true,
      text: '**bold** it',
      selectionStart: 2,
      selectionEnd: 6,
    })
  })

  it('wraps in italic with underscores', () => {
    expect(applied('x', 0, 1, 'italic').text).toBe('_x_')
  })

  it('combines bold and italic from chained clicks', () => {
    const bold = applied('x', 0, 1, 'bold')
    const both = applied(bold.text, bold.selectionStart, bold.selectionEnd, 'italic')
    expect(both.text).toBe('**_x_**')
  })

  it('wraps in underline markers', () => {
    expect(applied('x', 0, 1, 'underline').text).toBe('^^x^^')
  })

  it('wraps in strikethrough markers', () => {
    expect(applied('x', 0, 1, 'strike').text).toBe('~~x~~')
  })

  it('wraps in spoiler markers', () => {
    expect(applied('x', 0, 1, 'spoiler').text).toBe('%%x%%')
  })

  it('excludes surrounding whitespace from the wrap', () => {
    expect(applied('word ', 0, 5, 'bold')).toEqual({
      applied: true,
      text: '**word** ',
      selectionStart: 2,
      selectionEnd: 6,
    })
  })

  it('inserts a marker pair around a collapsed selection', () => {
    expect(applied('', 0, 0, 'bold')).toEqual({
      applied: true,
      text: '****',
      selectionStart: 2,
      selectionEnd: 2,
    })
  })

  it('wraps inline code in backticks', () => {
    expect(applied('use x()', 4, 7, 'inline-code')).toEqual({
      applied: true,
      text: 'use `x()`',
      selectionStart: 5,
      selectionEnd: 8,
    })
  })

  it('uses a longer delimiter and padding when the content has backticks', () => {
    expect(applied('`a', 0, 2, 'inline-code')).toEqual({
      applied: true,
      text: '`` `a ``',
      selectionStart: 3,
      selectionEnd: 5,
    })
  })

  it('wraps full lines in a code fence', () => {
    expect(applied('line1\nline2', 0, 11, 'code-block')).toEqual({
      applied: true,
      text: '```\nline1\nline2\n```',
      selectionStart: 4,
      selectionEnd: 15,
    })
  })

  it('expands a partial line selection to full lines for a code block', () => {
    expect(applied('abc\ndef', 1, 5, 'code-block').text).toBe('```\nabc\ndef\n```')
  })

  it('prefixes every selected line with a quote marker', () => {
    expect(applied('a\nb', 0, 3, 'quote')).toEqual({
      applied: true,
      text: '> a\n> b',
      selectionStart: 0,
      selectionEnd: 7,
    })
  })

  it('quotes only the current line for a collapsed selection', () => {
    expect(applied('x\ny\nz', 2, 2, 'quote').text).toBe('x\n> y\nz')
  })

  it('quotes blank lines inside the selection', () => {
    expect(applied('a\n\nb', 0, 4, 'quote').text).toBe('> a\n> \n> b')
  })
})

describe('applyFormat toggling', () => {
  it('unwraps bold when the markers already surround the selection', () => {
    expect(applied('**bold** x', 2, 6, 'bold')).toEqual({
      applied: true,
      text: 'bold x',
      selectionStart: 0,
      selectionEnd: 4,
    })
  })

  it('does not mistake underscore bold markers for italic', () => {
    expect(applied('__text__', 2, 6, 'italic').text).toBe('___text___')
  })

  it('unwraps italic', () => {
    expect(applied('_x_', 1, 2, 'italic').text).toBe('x')
  })

  it('unwraps only the italic layer of underscore bold italic', () => {
    expect(applied('___text___', 3, 7, 'italic').text).toBe('__text__')
  })

  it('unquotes fully quoted lines', () => {
    expect(applied('> a\n> b', 0, 7, 'quote')).toEqual({
      applied: true,
      text: 'a\nb',
      selectionStart: 0,
      selectionEnd: 3,
    })
  })

  it('unwraps inline code', () => {
    expect(applied('`x`', 1, 2, 'inline-code')).toEqual({
      applied: true,
      text: 'x',
      selectionStart: 0,
      selectionEnd: 1,
    })
  })

  it('unwraps a code block when the content is selected', () => {
    expect(applied('```\ncode\n```', 4, 8, 'code-block')).toEqual({
      applied: true,
      text: 'code',
      selectionStart: 0,
      selectionEnd: 4,
    })
  })

  it('unwraps a code block when the selection includes the fences', () => {
    expect(applied('```\ncode\n```', 0, 12, 'code-block').text).toBe('code')
  })
})

describe('applyFormat constraints', () => {
  it('refuses bold over inline code', () => {
    expect(refused('`x`', 0, 3, 'bold').reason).toBe(REFUSAL.inlineCode)
  })

  it('refuses bold inside a code block', () => {
    expect(refused('```\ncode\n```', 4, 8, 'bold').reason).toBe(REFUSAL.blockCode)
  })

  it('refuses bold for a caret inside an inline code span', () => {
    expect(refused('`code`', 3, 3, 'bold').reason).toBe(REFUSAL.inlineCode)
  })

  it('allows a spoiler around a whole inline code span', () => {
    expect(applied('`x` y', 0, 5, 'spoiler').text).toBe('%%`x` y%%')
  })

  it('refuses a spoiler over part of an inline code span', () => {
    expect(refused('a `code` b', 0, 5, 'spoiler').reason).toBe(REFUSAL.partialCode)
  })

  it('refuses a spoiler inside a code block', () => {
    expect(refused('```\nx\n```', 4, 5, 'spoiler').reason).toBe(REFUSAL.blockCode)
  })

  it('refuses quoting a line that contains inline code', () => {
    expect(refused('see `x`', 0, 3, 'quote').reason).toBe(REFUSAL.inlineCode)
  })

  it('refuses inline code over an existing code span', () => {
    expect(refused('a `x` b', 0, 7, 'inline-code').reason).toBe(REFUSAL.inlineCode)
  })

  it('refuses inline code over a multiline selection', () => {
    expect(refused('ab\ncd', 0, 5, 'inline-code').reason).toBe(REFUSAL.multilineInlineCode)
  })

  it('refuses inline formatting across a blank line', () => {
    expect(refused('a\n\nb', 0, 4, 'bold').reason).toBe(REFUSAL.blankLine)
  })

  it('refuses a code block over an existing fence', () => {
    expect(refused('x\n```\ny\n```', 0, 10, 'code-block').reason).toBe(REFUSAL.blockCode)
  })

  it('allows a code block over a line with inline code', () => {
    expect(applied('see `x`', 0, 7, 'code-block').text).toBe('```\nsee `x`\n```')
  })
})

describe('applyFormat escaping', () => {
  it('escapes markdown characters in the selection', () => {
    expect(applied('**x** _y_', 0, 9, 'escape')).toEqual({
      applied: true,
      text: '\\*\\*x\\*\\* \\_y\\_',
      selectionStart: 0,
      selectionEnd: 15,
    })
  })

  it('leaves already escaped characters untouched', () => {
    expect(applied('\\*a*', 0, 4, 'escape').text).toBe('\\*a\\*')
  })

  it('unescapes a fully escaped selection', () => {
    expect(applied('\\*\\*x\\*\\*', 0, 9, 'escape').text).toBe('**x**')
  })

  it('escapes post references', () => {
    expect(applied('>>123', 0, 5, 'escape').text).toBe('\\>\\>123')
  })

  it('refuses escaping inside inline code', () => {
    expect(refused('`a*b`', 0, 5, 'escape').reason).toBe(REFUSAL.codeLiteral)
  })

  it('refuses escaping inside a code block', () => {
    expect(refused('```\n*x*\n```', 4, 7, 'escape').reason).toBe(REFUSAL.codeLiteral)
  })

  it('refuses when nothing needs escaping', () => {
    expect(refused('hello', 0, 5, 'escape').reason).toBe(REFUSAL.nothingToEscape)
  })
})

describe('checkFormat', () => {
  it('returns null when the format is allowed', () => {
    expect(checkFormat('hello', 0, 5, 'bold')).toBeNull()
  })

  it('returns the refusal reason when the format is not allowed', () => {
    expect(checkFormat('`x`', 0, 3, 'bold')).toBe(REFUSAL.inlineCode)
  })
})
