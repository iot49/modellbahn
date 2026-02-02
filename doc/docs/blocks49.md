# Model Railroad Block Occupancy Detection

Just like prototype railroads, model railroads benefit from block detection to improve safety and enable automation. 

A multitude of solutions have been proposed. Generally they all are associated with often complex and expensive hardware and wiring.

The `blocks49` instead relies on an overhead camera to locate trains. A single camera can detect trains in many locations without additional hardware. The limitation is that this does not work in tunnels or underground shadow yards but is particularly suited for stations and other parts of the layout with dense tracks.

## API Keys

### Cloudflare KEY

A new Cloudflare key is likely NOT required.

If you are using wrangler login on your local machine, your credentials will work for the new blocks49 project automatically.

If you use a CLOUDFLARE_API_TOKEN:

Check if it is scoped to All Projects. If so, it will work.
If it is scoped to only the rails49 project, you will need to add permissions for the new blocks49 project or create a new token.

### Google Drive

1. Google Cloud Console Setup
  * Go to the Google Cloud Console.
  * Create a new project named blocks49 (or rename the current one).
  * Go to APIs & Services > Library and enable the Google Drive API.
  * Go to APIs & Services > OAuth consent screen:
    * Choose External (unless you have a Google Workspace org).
    * Add the scope: https://www.googleapis.com/auth/drive.file.
    * Add your email as a Test User (required for "Testing" status).
2. Create Credentials
  * Go to APIs & Services > Credentials.
  * Click Create Credentials > OAuth client ID.
  * Select Desktop App as the Application type.
Copy your Client ID and Client Secret.
3. Update Local Config
Update `server/.env` with the new values:

```
BLOCKS49_EXPORT_CLIENT_ID="your-new-client-id"
BLOCKS49_EXPORT_CLIENT_SECRET="your-new-client-secret"
```