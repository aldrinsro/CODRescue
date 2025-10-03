/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */
export default {
  async fetch(request: Request, env: { TUNNEL_URL: string }) {
    try {
      const targetBase = env.TUNNEL_URL;
      if (!targetBase) {
        return new Response('Missing TUNNEL_URL secret', { status: 500 });
      }

      const incomingUrl = new URL(request.url);

      // Ignorer l'endpoint d'auto-reload qui génère du bruit via tunnel
      if (incomingUrl.pathname.startsWith('/__reload__/')) {
        return new Response(null, { status: 204 });
      }

      const targetUrl = new URL(incomingUrl.pathname + incomingUrl.search, targetBase);

      // Préparer les en-têtes pour l'origin
      const headers = new Headers(request.headers);
      headers.delete('host');
      headers.set('X-Forwarded-Proto', 'https');
      headers.set('X-Forwarded-Host', incomingUrl.host);
      const cfConnectingIp = request.headers.get('CF-Connecting-IP') || request.headers.get('x-real-ip') || '';
      if (cfConnectingIp) headers.set('X-Forwarded-For', cfConnectingIp);
      // Éviter les encodages non supportés par l'origin
      headers.set('Accept-Encoding', 'identity');

      const method = request.method.toUpperCase();
      const hasBody = !(method === 'GET' || method === 'HEAD');
      const bufferedBody = hasBody ? await request.arrayBuffer() : undefined;

      // Utiliser des redirections manuelles pour que le navigateur gère Set-Cookie sur 302
      const response = await fetch(targetUrl.toString(), {
        method,
        headers,
        body: bufferedBody,
        redirect: 'manual',
      });

      // Pass-through complet de la réponse (y compris Set-Cookie et Location)
      const respHeaders = new Headers(response.headers);
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: respHeaders,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return new Response('Proxy error: ' + message, { status: 502 });
    }
  },
};