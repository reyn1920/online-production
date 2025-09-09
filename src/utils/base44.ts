// src/utils/base44.ts

/**
 * Base44 Encoder - A custom encoding system for text export
 * Provides a compact, URL-safe encoding for text data
 */

const BASE44_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh';
const BASE = BASE44_ALPHABET.length;

/**
 * Encodes a string to Base44 format
 * @param text - The text to encode
 * @returns Base44 encoded string
 */
export function base44Encode(text: string): string {
  if (!text) return '';

  // Convert string to bytes
  const bytes = new TextEncoder().encode(text);

  // Convert bytes to a big integer
  let num = BigInt(0);
  for (let i = 0; i < bytes.length; i++) {
    num = num * BigInt(256) + BigInt(bytes[i]);
  }

  // Convert to base44
  if (num === BigInt(0)) return BASE44_ALPHABET[0];

  let result = '';
  while (num > 0) {
    result = BASE44_ALPHABET[Number(num % BigInt(BASE))] + result;
    num = num / BigInt(BASE);
  }

  return result;
}

/**
 * Decodes a Base44 string back to original text
 * @param encoded - The Base44 encoded string
 * @returns Original decoded text
 */
export function base44Decode(encoded: string): string {
  if (!encoded) return '';

  // Convert base44 to big integer
  let num = BigInt(0);
  for (let i = 0; i < encoded.length; i++) {
    const char = encoded[i];
    const index = BASE44_ALPHABET.indexOf(char);
    if (index === -1) {
      throw new Error(`Invalid Base44 character: ${char}`);
    }
    num = num * BigInt(BASE) + BigInt(index);
  }

  // Convert big integer to bytes
  if (num === BigInt(0)) return '';

  const bytes: number[] = [];
  while (num > 0) {
    bytes.unshift(Number(num % BigInt(256)));
    num = num / BigInt(256);
  }

  // Convert bytes to string
  return new TextDecoder().decode(new Uint8Array(bytes));
}

/**
 * Creates a Base44 export of any data object
 * @param data - The data to export
 * @param label - Optional label for the export
 * @returns Base44 encoded export string
 */
export function createBase44Export(data: any, label?: string): string {
  const exportData = {
    label: label || 'Data Export',
    timestamp: new Date().toISOString(),
    data: data,
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  return base44Encode(jsonString);
}

/**
 * Parses a Base44 export back to the original data
 * @param encoded - The Base44 encoded export
 * @returns Parsed export data with metadata
 */
export function parseBase44Export(encoded: string): {
  label: string;
  timestamp: string;
  data: any;
} {
  const decoded = base44Decode(encoded);
  return JSON.parse(decoded);
}

/**
 * Validates if a string is valid Base44
 * @param str - String to validate
 * @returns True if valid Base44
 */
export function isValidBase44(str: string): boolean {
  if (!str) return false;

  for (let i = 0; i < str.length; i++) {
    if (BASE44_ALPHABET.indexOf(str[i]) === -1) {
      return false;
    }
  }

  return true;
}

/**
 * Gets compression ratio of Base44 encoding
 * @param originalText - Original text
 * @returns Compression ratio (encoded length / original length)
 */
export function getCompressionRatio(originalText: string): number {
  if (!originalText) return 0;

  const encoded = base44Encode(originalText);
  return encoded.length / originalText.length;
}

/**
 * Utility for exporting entity data in Base44 format
 * @param entityName - Name of the entity
 * @param entityData - The entity data to export
 * @returns Base44 encoded entity export
 */
export function exportEntityAsBase44(entityName: string, entityData: any[]): string {
  return createBase44Export(entityData, `${entityName} Export`);
}

/**
 * Utility for creating shareable Base44 links
 * @param data - Data to share
 * @param baseUrl - Base URL for the share link
 * @returns Complete shareable URL with Base44 data
 */
export function createShareableLink(data: any, baseUrl: string = window.location.origin): string {
  const encoded = createBase44Export(data, 'Shared Data');
  return `${baseUrl}?data=${encodeURIComponent(encoded)}`;
}

/**
 * Extracts Base44 data from a shareable URL
 * @param url - The URL containing Base44 data
 * @returns Parsed data or null if not found
 */
export function extractFromShareableLink(url: string): any | null {
  try {
    const urlObj = new URL(url);
    const encodedData = urlObj.searchParams.get('data');

    if (!encodedData) return null;

    const decoded = decodeURIComponent(encodedData);
    return parseBase44Export(decoded);
  } catch (error) {
    console.error('Failed to extract data from shareable link:', error);
    return null;
  }
}
