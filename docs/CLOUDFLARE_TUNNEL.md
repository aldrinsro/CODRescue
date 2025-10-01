![1758657834961](image/CLOUDFLARE_TUNNEL/1758657834961.png)## Cloudflare Tunnel (cloudflared) — Exposer Django partout

Ce guide explique comment installer, configurer et utiliser Cloudflare Tunnel pour exposer votre application Django en développement ou en démonstration, sans ouvrir de ports.

Important: ce document couvre aussi un Worker Cloudflare `yz-tunnel-redirect` servant d’URL stable gratuite (`*.workers.dev`) qui proxifie vers l’URL éphémère `*.trycloudflare.com`.

### 1) Prérequis

- Windows 10/11
- Python/Django opérationnel
- Port local: `http://localhost:8000` (ou autre)

### 2) Installation de cloudflared

Option 1 — via Winget:

```powershell
winget install cloudflare.cloudflared
```

Vérifier la version (chemin direct si non dans PATH):

```powershell
cloudflared --version
# ou, si non reconnu:
"C:\Users\<votre_user>\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe" --version
```

Ajouter au PATH (session courante):

```powershell
$env:PATH += ";C:\Users\<votre_user>\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe"
```

Pour l’ajout permanent:

```powershell
setx PATH "$($env:PATH);C:\Users\<votre_user>\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe"
```

### 3) Configuration Django (CORS/CSRF)

Dans `config/settings.py`, assurez-vous d’avoir:

- CORS ouvert en dev ou regex des domaines de tunnel:

```python
CORS_ALLOW_ALL_ORIGINS = True  # dev
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://[a-z0-9-]+\.trycloudflare\.com$',
    r'^https://[a-z0-9-]+\.workers\.dev$',
]
```

- Origines CSRF de confiance (HTTPS):

```python
CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
    'https://*.workers.dev',
]
```

- Django derrière un proxy HTTPS (Workers + Tunnel):

```python
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

Note: En production, resserrez `CORS_ALLOWED_ORIGINS` et `CSRF_TRUSTED_ORIGINS` aux seuls domaines utilisés.

### 4) Démarrer un tunnel éphémère (rapide)

Dans un terminal:

```powershell
python manage.py runserver 8000
cloudflared tunnel --url http://localhost:8000
```

Cloudflare affichera une URL publique du type:

```
https://xxxxx.trycloudflare.com
```

Ouvrez cette URL en navigation privée (ou videz les cookies du domaine) pour éviter les conflits de cookies/CSRF.

### 5) Créer une URL stable via Cloudflare Workers (gratuit)

But: obtenir `https://<sous-domaine>.workers.dev` stable, qui proxifie vers l’URL `*.trycloudflare.com` courante.

1) Installer Wrangler v2+:

```powershell
npm install -g wrangler
wrangler --version
```

2) Se connecter:

```powershell
wrangler login
```

3) Créer le projet Worker:

```powershell
wrangler init yz-tunnel-redirect --yes
cd yz-tunnel-redirect
```

Choisir « Worker only » et « TypeScript » si demandé.

4) Remplacer le code du Worker par un proxy (fichier `src/index.ts`):

```ts
export default {
  async fetch(request: Request, env: { TUNNEL_URL: string }) {
    try {
      const targetBase = env.TUNNEL_URL;
      if (!targetBase) return new Response('Missing TUNNEL_URL secret', { status: 500 });

      const incomingUrl = new URL(request.url);
      // Ignore l’auto-reload en dev
      if (incomingUrl.pathname.startsWith('/__reload__/')) return new Response(null, { status: 204 });

      const targetUrl = new URL(incomingUrl.pathname + incomingUrl.search, targetBase);

      const headers = new Headers(request.headers);
      headers.delete('host');
      // Contexte proxy HTTPS pour Django
      headers.set('X-Forwarded-Proto', 'https');
      headers.set('X-Forwarded-Host', incomingUrl.host);
      const cfIp = request.headers.get('CF-Connecting-IP') || request.headers.get('x-real-ip') || '';
      if (cfIp) headers.set('X-Forwarded-For', cfIp);
      headers.set('Accept-Encoding', 'identity');

      const method = request.method.toUpperCase();
      const hasBody = !(method === 'GET' || method === 'HEAD');
      const bufferedBody = hasBody ? await request.arrayBuffer() : undefined;

      // Redirections « manual » pour préserver Set-Cookie/Location
      const response = await fetch(targetUrl.toString(), {
        method,
        headers,
        body: bufferedBody,
        redirect: 'manual',
      });

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: new Headers(response.headers),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return new Response('Proxy error: ' + msg, { status: 502 });
    }
  },
};
```

5) Premier déploiement et sous-domaine workers.dev:

```powershell
wrangler deploy
# Si demandé, enregistrer un sous-domaine, ex: yzrescue => yzrescue.workers.dev
```

6) Récupérer l’URL du tunnel Cloudflare actuel (dans la fenêtre `cloudflared`) et l’enregistrer en secret:

```powershell
echo https://xxxxx.trycloudflare.com | wrangler secret put TUNNEL_URL
```

7) Tester l’URL stable:

```
https://yz-tunnel-redirect.<votre-sous-domaine>.workers.dev/login/
```

À chaque nouveau tunnel (l’URL `*.trycloudflare.com` change), mettre à jour uniquement le secret:

```powershell
wrangler secret put TUNNEL_URL
# ou non interactif
echo https://nouveau.trycloudflare.com | wrangler secret put TUNNEL_URL
```

Pas besoin de redéployer si le code ne change pas.

### 6) Tunnel nommé (persistant) avec votre domaine (optionnel)

Nécessite un compte Cloudflare et un domaine géré par Cloudflare.

```powershell
cloudflared login
cloudflared tunnel create yz-django
cloudflared tunnel route dns yz-django sousdomaine.votredomaine.com
```

Fichier `%USERPROFILE%\.cloudflared\config.yml` minimal:

```yaml
tunnel: yz-django
credentials-file: C:\Users\<votre_user>\.cloudflared\<id>.json
ingress:
  - hostname: sousdomaine.votredomaine.com
    service: http://localhost:8000
  - service: http_status:404
```

Lancer:

```powershell
cloudflared tunnel run yz-django
```

### 7) Dépannage

- 403 CSRF depuis le tunnel:
  - Vérifier `CSRF_TRUSTED_ORIGINS` contient le domaine (ex: `https://*.trycloudflare.com`).
  - Vider cookies/cache du domaine.
  - S’assurer que les formulaires POST incluent `{% csrf_token %}` et que les requêtes AJAX envoient l’en-tête `X-CSRFToken`.
  - Vérifier les en-têtes proxy: `X-Forwarded-Proto: https`, `X-Forwarded-Host` et les cookies `Secure`/`SameSite=Lax`.
- Tunnel non joignable les premières secondes: attendre 10–30 s après la création.
- Garder la fenêtre `cloudflared` ouverte (Ctrl+C pour arrêter).
- Erreur 1101 (Worker threw exception): déployer avec le code proxy ci-dessus et vérifier que `TUNNEL_URL` est défini.
- Erreur 1016/1033: l’URL `trycloudflare` utilisée est incomplète/ancienne. Copier l’URL exacte affichée par `cloudflared` (terminant par `.trycloudflare.com`) et ré-exécuter `wrangler secret put TUNNEL_URL`.
- Boucle/bloque au login: vérifier `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, cookies `Secure` et `SameSite`.
- Bruit `/__reload__/events/`: le Worker ignore cet endpoint; vous pouvez aussi désactiver `django_browser_reload` côté Django pour un accès public.

### 8) Sécurité (prod)

- Mettre `DEBUG = False`.
- Restreindre `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` au domaine final.
- Forcer HTTPS côté client; `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`.

---

Dernière mise à jour: 2025-09-23

### Annexe — Comparaison: Cloudflare Tunnel vs ngrok

- Connexions/limites gratuites

  - ngrok (gratuit): limites sur connexions simultanées et bande passante; URL change à chaque démarrage (sauf compte payant/domains réservés).
  - Cloudflare Tunnel «quick tunnel» (gratuit, sans compte): URL éphémère, pas de SLO; Cloudflare peut résilier; adapté aux démos/tests.
  - Cloudflare Tunnel nommé (gratuit avec compte): domaine stable via DNS Cloudflare, pas de limite de connexions comparable à l’offre gratuite ngrok pour un usage dev/POC.
- Domaine et stabilité

  - ngrok: domaine aléatoire en gratuit; domaine réservé en payant.
  - Cloudflare: domaine aléatoire `trycloudflare.com` pour quick tunnel; domaine personnalisé stable via tunnel nommé + DNS Cloudflare.
- Mise en place

  - ngrok: exécutable unique, `ngrok http 8000`.
  - Cloudflare: `cloudflared tunnel --url http://localhost:8000` (éphémère) ou configuration tunnel nommé (`cloudflared login`, DNS, `config.yml`).
- TLS et proxy

  - ngrok: TLS géré côté ngrok, back-end en HTTP local.
  - Cloudflare: TLS géré par Cloudflare; options avancées (WAF, Argo, Access) si compte.
- Authentification/contrôle d’accès

  - ngrok: protections simples en gratuit; plus d’options en payant.
  - Cloudflare: Cloudflare Access (SSO, policies) avec compte.
- Coûts

  - ngrok: plan gratuit limité; fonctionnalités stables/URL personnalisées nécessitent un plan payant.
  - Cloudflare: quick tunnel gratuit; tunnel nommé gratuit avec compte, coûts éventuels selon options (WAF/Access/Argo).

En bref: pour des démos rapides, les deux conviennent. Pour un point d’accès stable et sans limites strictes sur les connexions en dev/POC, un tunnel Cloudflare nommé avec domaine Cloudflare est souvent plus flexible que l’offre gratuite ngrok.

### Annexe — Rendre cloudflared et wrangler accessibles partout (PATH)

Objectif: rendre `cloudflared` et `wrangler` utilisables depuis toutes les sessions PowerShell et CMD, quel que soit le dossier ou l’environnement Python actif.

1) Prérequis

- Windows 10 ou supérieur
- PowerShell
- Node.js et npm (pour Wrangler)
- Droits administrateur pour modifier le PATH système

2) Installation des outils

- Cloudflared via WinGet (ou téléchargement officiel). Localiser l’exécutable, ex:

```
C:\Users\jesse\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe
```

Vérifier:

```powershell
& "C:\Users\jesse\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe" --version
```

- Wrangler (dernière version):

```powershell
npm install -g wrangler
wrangler --version
```

Si une ancienne v1 est présente:

```powershell
npm uninstall -g @cloudflare/wrangler
npm install -g wrangler
```

Trouver le dossier npm global:

```powershell
npm config get prefix
# ex: C:\Users\jesse\AppData\Roaming\npm
```

3) Ajouter au PATH système (permanent)
   Ouvrir PowerShell en Administrateur puis:

```powershell
$newPaths = "C:\Users\jesse\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe","C:\Users\jesse\AppData\Roaming\npm"
$current = [Environment]::GetEnvironmentVariable("Path","Machine")
[Environment]::SetEnvironmentVariable("Path", ($current + ";" + ($newPaths -join ";")), "Machine")
```

Fermer toutes les consoles et rouvrir. Vérifier:

```powershell
cloudflared --version
wrangler --version
```

4) Astuce PowerShell: alias permanent (optionnel)
   Dans votre profil PowerShell:

```powershell
notepad $PROFILE
# Ajouter:
Set-Alias cloudflared "C:\Users\jesse\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
Set-Alias wrangler "C:\Users\jesse\AppData\Roaming\npm\wrangler.cmd"
```

Dans une nouvelle session, `cloudflared` et `wrangler` seront disponibles automatiquement.

5) Résumé

- Outils accessibles globalement dans toutes les sessions et dossiers.
- Chemins ajoutés au PATH système pour tous les utilisateurs.
- Alias PowerShell pour compatibilité maximale, même avec des virtualenvs.

### Automatisation recommandée — Script PowerShell pour URL stable Workers

Objectif: avoir une URL publique stable `*.workers.dev` et mettre à jour automatiquement le secret `TUNNEL_URL` à chaque lancement d’un quick tunnel `*.trycloudflare.com`.

Fichier: `scripts/Start-YZTunnel.ps1`

Usage:
1) Prérequis dans le PATH:
   - `cloudflared`
   - `wrangler` (ou fournis via paramètres)
2) Lancer Django:
```powershell
python manage.py runserver 8000
```
3) Lancer le script:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-YZTunnel.ps1
```

Options utiles:
```powershell
# Port différent
powershell -ExecutionPolicy Bypass -File .\scripts\Start-YZTunnel.ps1 -LocalUrl "http://localhost:9000"

# Chemins explicites si PATH non configuré
powershell -ExecutionPolicy Bypass -File .\scripts\Start-YZTunnel.ps1 `
  -Wrangler "$env:APPDATA\npm\wrangler.cmd" `
  -Cloudflared "C:\\Users\\jesse\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\\cloudflared.exe"
```

Le script:
- Démarre `cloudflared tunnel --url <LocalUrl>` et écrit les logs.
- Détecte l’URL `https://<...>.trycloudflare.com` dans les logs.
- Met à jour le secret Worker `TUNNEL_URL` via `wrangler secret put`.
- Laisse le tunnel tourner; l’URL stable `https://yz-tunnel-redirect.<sous-domaine>.workers.dev/` devient immédiatement utilisable.

Conseils:
- Ajouter `cloudflared` et `wrangler` au PATH utilisateur pour éviter les chemins absolus.
- Créer un raccourci Windows vers la commande d’exécution pour un démarrage en 1 clic.
