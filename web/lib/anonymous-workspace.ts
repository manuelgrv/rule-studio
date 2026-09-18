const COOKIE = 'rule_studio_workspace';

export function workspaceToken(request: Request): string | null {
  const value = request.headers.get('cookie')?.split(';')
    .map((part) => part.trim()).find((part) => part.startsWith(`${COOKIE}=`))
    ?.slice(COOKIE.length + 1);
  return value && /^[a-f0-9]{64}$/.test(value) ? value : null;
}

export function newWorkspaceToken(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)),
    (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function workspaceOwner(token: string): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return 'anonymous:' + Array.from(new Uint8Array(hash),
    (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export function workspaceCookie(token: string, request: Request): string {
  const secure = new URL(request.url).protocol === 'https:' ? '; Secure' : '';
  return `${COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000${secure}`;
}
