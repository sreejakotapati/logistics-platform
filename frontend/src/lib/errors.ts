import type { ApiError } from '@/types';

export function errorMessage(e: unknown, fallback = 'Something went wrong'): string {
  if (e && typeof e === 'object' && 'message' in e) {
    return String((e as ApiError).message) || fallback;
  }
  return fallback;
}
