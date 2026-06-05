import type { components } from '@/api/schema'

// friendly aliases for the generated schema types so the rest of the app
// imports from one place and never touches components['schemas'][...] directly
type Schemas = components['schemas']

export type BoardResponse = Schemas['BoardResponse']
export type OpPostPreview = Schemas['OpPostPreview']
export type ThreadResponse = Schemas['ThreadResponse']
export type ThreadDetailResponse = Schemas['ThreadDetailResponse']
export type PostResponse = Schemas['PostResponse']
export type PostEditResponse = Schemas['PostEditResponse']
export type AttachmentResponse = Schemas['AttachmentResponse']
export type ReportResponse = Schemas['ReportResponse']
export type BanResponse = Schemas['BanResponse']
export type TokenResponse = Schemas['TokenResponse']
export type CaptchaChallengeResponse = Schemas['CaptchaChallengeResponse']
export type ModRole = Schemas['ModRole']

export type BoardCreate = Schemas['BoardCreate']
export type BoardUpdate = Schemas['BoardUpdate']
export type BoardReorder = Schemas['BoardReorder']
export type PostEditCreate = Schemas['PostEditCreate']
export type ReportCreate = Schemas['ReportCreate']
export type BanCreate = Schemas['BanCreate']
export type ModLogin = Schemas['ModLogin']
