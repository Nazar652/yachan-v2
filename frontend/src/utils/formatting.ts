export type TextFormat =
  | 'bold'
  | 'italic'
  | 'underline'
  | 'strike'
  | 'spoiler'
  | 'inline-code'
  | 'code-block'
  | 'quote'
  | 'escape'

export interface FormatApplication {
  text: string
  selectionStart: number
  selectionEnd: number
}

export type FormatOutcome = ({ applied: true } & FormatApplication) | { applied: false; reason: string }

export interface Region {
  start: number
  end: number
}

export interface CodeRegions {
  inline: Region[]
  block: Region[]
}

export const REFUSAL = {
  inlineCode: 'inline code can only be wrapped in a spoiler',
  blockCode: 'a code block cannot be combined with other formatting',
  partialCode: 'select the whole code span to wrap it in a spoiler',
  blankLine: 'inline formatting cannot span an empty line',
  multilineInlineCode: 'use the code block button for multiline code',
  codeLiteral: 'code is rendered literally, escaping is not needed',
  nothingToEscape: 'nothing in the selection needs escaping',
} as const

const FENCE_OPEN_RE = /^ {0,3}(`{3,}|~{3,})/
const FENCE_CLOSE_RE = /^ {0,3}(`{3,}|~{3,})[ \t]*$/

const INLINE_MARKERS = {
  bold: '**',
  italic: '_',
  underline: '^^',
  strike: '~~',
  spoiler: '%%',
} as const

const ESCAPE_TOKEN_RE = /\\[\\`*_~^%>[\]#]|[\\`*_~^%>[\]#]/g

const UNWRAP_CHARACTERS = {
  bold: '*',
  underline: '^',
  strike: '~',
  spoiler: '%',
} as const

type InlineWrapFormat = keyof typeof INLINE_MARKERS

export function findCodeRegions(text: string): CodeRegions {
  const block: Region[] = []
  const lines = text.split('\n')

  let offset = 0
  let openFence: { character: string; length: number; start: number } | null = null
  for (const line of lines) {
    const lineEnd = offset + line.length
    if (openFence) {
      const closeMarker = FENCE_CLOSE_RE.exec(line)?.[1]
      if (closeMarker && closeMarker.charAt(0) === openFence.character && closeMarker.length >= openFence.length) {
        block.push({ start: openFence.start, end: lineEnd })
        openFence = null
      }
    } else {
      const openMarker = FENCE_OPEN_RE.exec(line)?.[1]
      if (openMarker) {
        openFence = { character: openMarker.charAt(0), length: openMarker.length, start: offset }
      }
    }
    offset = lineEnd + 1
  }
  if (openFence) {
    block.push({ start: openFence.start, end: text.length })
  }

  const runs: Region[] = []
  const backtickRun = /`+/g
  for (let match = backtickRun.exec(text); match !== null; match = backtickRun.exec(text)) {
    const run = { start: match.index, end: match.index + match[0].length }
    if (!block.some((region) => run.start >= region.start && run.start < region.end)) {
      runs.push(run)
    }
  }

  // commonmark-style pairing: an opener closes at the next run of the same
  // length; spans cannot cross a blank line (paragraph boundary)
  const inline: Region[] = []
  let index = 0
  while (index < runs.length) {
    const opener = runs[index]
    if (!opener) break
    const openerLength = opener.end - opener.start
    let closerIndex = -1
    let closer: Region | null = null
    for (let candidate = index + 1; candidate < runs.length; candidate += 1) {
      const candidateRun = runs[candidate]
      if (candidateRun && candidateRun.end - candidateRun.start === openerLength) {
        closerIndex = candidate
        closer = candidateRun
        break
      }
    }
    if (closer && !hasBlankLine(text.slice(opener.end, closer.start))) {
      inline.push({ start: opener.start, end: closer.end })
      index = closerIndex + 1
    } else {
      index += 1
    }
  }

  return { inline, block }
}

export function checkFormat(
  text: string,
  selectionStart: number,
  selectionEnd: number,
  format: TextFormat,
): string | null {
  const { start, end } = normalizeRange(text, selectionStart, selectionEnd, format)
  const regions = findCodeRegions(text)

  if (regions.block.some((region) => intersects(region, start, end))) {
    return format === 'escape' ? REFUSAL.codeLiteral : REFUSAL.blockCode
  }
  const inlineHits = regions.inline.filter((region) => intersects(region, start, end))

  switch (format) {
    case 'bold':
    case 'italic':
    case 'underline':
    case 'strike':
      if (inlineHits.length > 0) return REFUSAL.inlineCode
      if (hasBlankLine(text.slice(start, end))) return REFUSAL.blankLine
      return null
    case 'quote':
      if (inlineHits.length > 0) return REFUSAL.inlineCode
      return null
    case 'spoiler':
      if (inlineHits.some((region) => region.start < start || region.end > end)) return REFUSAL.partialCode
      if (hasBlankLine(text.slice(start, end))) return REFUSAL.blankLine
      return null
    case 'inline-code':
      if (inlineHits.length > 0) return REFUSAL.inlineCode
      if (text.slice(start, end).includes('\n')) return REFUSAL.multilineInlineCode
      return null
    case 'code-block':
      return null
    case 'escape':
      if (inlineHits.length > 0) return REFUSAL.codeLiteral
      return null
  }
}

export function applyFormat(
  text: string,
  selectionStart: number,
  selectionEnd: number,
  format: TextFormat,
): FormatOutcome {
  const { start, end } = normalizeRange(text, selectionStart, selectionEnd, format)

  // code unwraps must run before the constraint check: the selection sits
  // inside the very code region the check would otherwise refuse
  if (format === 'inline-code') {
    const unwrapped = unwrapSurroundingCode(text, start, end)
    if (unwrapped) return { applied: true, ...unwrapped }
  }
  if (format === 'code-block') {
    const unwrapped = unwrapCodeBlock(text, start, end)
    if (unwrapped) return { applied: true, ...unwrapped }
  }

  const reason = checkFormat(text, start, end, format)
  if (reason) return { applied: false, reason }

  switch (format) {
    case 'quote':
      return { applied: true, ...applyQuote(text, start, end) }
    case 'code-block':
      return { applied: true, ...wrapCodeBlock(text, start, end) }
    case 'inline-code':
      return { applied: true, ...wrapInlineCode(text, start, end) }
    case 'escape': {
      const escaped = toggleEscape(text, start, end)
      if (!escaped) return { applied: false, reason: REFUSAL.nothingToEscape }
      return { applied: true, ...escaped }
    }
    default: {
      const unwrapped = unwrapSurroundingMarker(text, start, end, format)
      if (unwrapped) return { applied: true, ...unwrapped }
      return { applied: true, ...wrapInline(text, start, end, INLINE_MARKERS[format]) }
    }
  }
}

function hasBlankLine(value: string): boolean {
  return /\n[ \t]*\n/.test(value)
}

function intersects(region: Region, start: number, end: number): boolean {
  if (start === end) {
    return region.start < start && start < region.end
  }
  return region.start < end && start < region.end
}

function normalizeRange(text: string, selectionStart: number, selectionEnd: number, format: TextFormat): Region {
  const start = Math.max(0, Math.min(selectionStart, selectionEnd))
  const end = Math.min(text.length, Math.max(selectionStart, selectionEnd))
  if (format === 'quote' || format === 'code-block') {
    return expandToLines(text, start, end)
  }
  return trimWhitespace(text, start, end)
}

function expandToLines(text: string, start: number, end: number): Region {
  const effectiveEnd = end > start && text.charAt(end - 1) === '\n' ? end - 1 : end
  const lineStart = start === 0 ? 0 : text.lastIndexOf('\n', start - 1) + 1
  const newlineAfter = text.indexOf('\n', effectiveEnd)
  return { start: lineStart, end: newlineAfter === -1 ? text.length : newlineAfter }
}

function trimWhitespace(text: string, start: number, end: number): Region {
  let trimmedStart = start
  let trimmedEnd = end
  while (trimmedStart < trimmedEnd && /\s/.test(text.charAt(trimmedStart))) trimmedStart += 1
  while (trimmedEnd > trimmedStart && /\s/.test(text.charAt(trimmedEnd - 1))) trimmedEnd -= 1
  return { start: trimmedStart, end: trimmedEnd }
}

function runLengthBefore(text: string, position: number, character: string): number {
  let length = 0
  while (position - length - 1 >= 0 && text.charAt(position - length - 1) === character) length += 1
  return length
}

function runLengthAfter(text: string, position: number, character: string): number {
  let length = 0
  while (position + length < text.length && text.charAt(position + length) === character) length += 1
  return length
}

function removeSurrounding(text: string, start: number, end: number, count: number): FormatApplication {
  return {
    text: text.slice(0, start - count) + text.slice(start, end) + text.slice(end + count),
    selectionStart: start - count,
    selectionEnd: end - count,
  }
}

function unwrapSurroundingMarker(
  text: string,
  start: number,
  end: number,
  format: InlineWrapFormat,
): FormatApplication | null {
  // the underscore is also a bold marker (__bold__), so the adjacent run
  // length decides which layers are present: 1 = italic, 2 = bold, 3 = both
  if (format === 'italic') {
    const before = runLengthBefore(text, start, '_')
    const after = runLengthAfter(text, end, '_')
    if (before > 0 && after > 0 && Math.min(before, after) % 2 === 1) {
      return removeSurrounding(text, start, end, 1)
    }
    return null
  }
  const character = UNWRAP_CHARACTERS[format]
  if (runLengthBefore(text, start, character) >= 2 && runLengthAfter(text, end, character) >= 2) {
    return removeSurrounding(text, start, end, 2)
  }
  return null
}

function unwrapSurroundingCode(text: string, start: number, end: number): FormatApplication | null {
  const before = runLengthBefore(text, start, '`')
  const after = runLengthAfter(text, end, '`')
  if (before > 0 && before === after) {
    return removeSurrounding(text, start, end, before)
  }
  return null
}

function wrapInline(text: string, start: number, end: number, marker: string): FormatApplication {
  return {
    text: text.slice(0, start) + marker + text.slice(start, end) + marker + text.slice(end),
    selectionStart: start + marker.length,
    selectionEnd: end + marker.length,
  }
}

function wrapInlineCode(text: string, start: number, end: number): FormatApplication {
  const content = text.slice(start, end)
  let longestRun = 0
  for (const run of content.match(/`+/g) ?? []) {
    longestRun = Math.max(longestRun, run.length)
  }
  const delimiter = '`'.repeat(longestRun + 1)
  // commonmark: pad with spaces when the content starts or ends with a backtick
  const padding = content.startsWith('`') || content.endsWith('`') ? ' ' : ''
  const replacement = delimiter + padding + content + padding + delimiter
  const contentStart = start + delimiter.length + padding.length
  return {
    text: text.slice(0, start) + replacement + text.slice(end),
    selectionStart: contentStart,
    selectionEnd: contentStart + content.length,
  }
}

function wrapCodeBlock(text: string, start: number, end: number): FormatApplication {
  const content = text.slice(start, end)
  return {
    text: text.slice(0, start) + '```\n' + content + '\n```' + text.slice(end),
    selectionStart: start + 4,
    selectionEnd: start + 4 + content.length,
  }
}

function unwrapCodeBlock(text: string, start: number, end: number): FormatApplication | null {
  const content = text.slice(start, end)
  const lines = content.split('\n')

  // selection covering the whole block including its fence lines
  if (lines.length >= 2) {
    const openMarker = FENCE_OPEN_RE.exec(lines[0] ?? '')?.[1]
    const closeMarker = FENCE_CLOSE_RE.exec(lines[lines.length - 1] ?? '')?.[1]
    if (openMarker && closeMarker && closeMarker.charAt(0) === openMarker.charAt(0) && closeMarker.length >= openMarker.length) {
      const inner = lines.slice(1, -1).join('\n')
      return {
        text: text.slice(0, start) + inner + text.slice(end),
        selectionStart: start,
        selectionEnd: start + inner.length,
      }
    }
  }

  // selection covering only the content, with fence lines directly around it
  if (start === 0 || end === text.length || text.charAt(end) !== '\n') return null
  const openLineStart = start - 1 === 0 ? 0 : text.lastIndexOf('\n', start - 2) + 1
  const openLine = text.slice(openLineStart, start - 1)
  const closeNewline = text.indexOf('\n', end + 1)
  const closeLineEnd = closeNewline === -1 ? text.length : closeNewline
  const closeLine = text.slice(end + 1, closeLineEnd)
  const openMarker = FENCE_OPEN_RE.exec(openLine)?.[1]
  const closeMarker = FENCE_CLOSE_RE.exec(closeLine)?.[1]
  if (!openMarker || !closeMarker || closeMarker.charAt(0) !== openMarker.charAt(0) || closeMarker.length < openMarker.length) {
    return null
  }
  return {
    text: text.slice(0, openLineStart) + content + text.slice(closeLineEnd),
    selectionStart: openLineStart,
    selectionEnd: openLineStart + content.length,
  }
}

function toggleEscape(text: string, start: number, end: number): FormatApplication | null {
  const content = text.slice(start, end)
  const tokens = content.match(ESCAPE_TOKEN_RE) ?? []
  if (tokens.length === 0) return null
  const hasBare = tokens.some((token) => token.length === 1)
  const replacement = hasBare
    ? content.replace(ESCAPE_TOKEN_RE, (token) => (token.length === 2 ? token : `\\${token}`))
    : content.replace(ESCAPE_TOKEN_RE, (token) => token.slice(1))
  return {
    text: text.slice(0, start) + replacement + text.slice(end),
    selectionStart: start,
    selectionEnd: start + replacement.length,
  }
}

function applyQuote(text: string, start: number, end: number): FormatApplication {
  const lines = text.slice(start, end).split('\n')
  const allQuoted = lines.every((line) => /^> ?/.test(line))
  const changed = allQuoted
    ? lines.map((line) => line.replace(/^> ?/, ''))
    : lines.map((line) => `> ${line}`)
  const replacement = changed.join('\n')
  return {
    text: text.slice(0, start) + replacement + text.slice(end),
    selectionStart: start,
    selectionEnd: start + replacement.length,
  }
}
