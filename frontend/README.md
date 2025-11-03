# Company Dashboard Frontend (SvelteKit)

This is the SvelteKit frontend for the Company Data Dashboard. It is designed to:

* Connect to the backend API Gateway (Lambda) to fetch data.
* Display a high-speed "Summary" (from DynamoDB).
* Display detailed "Reports" (from RDS).
* Show the private IP of the EC2 instance serving the request (for debugging behind an ALB/ASG).

---

## 1.  Project Configuration

Before running, you **must** configure the environment variables.

1.  **Create a `.env` file** in the project's root directory (the same folder as `package.json`).
2.  Add your API Gateway Invoke URL to this file:

    ```ini
    # Replace with your API Gateway Invoke URL
    PUBLIC_API_BASE_URL="https://xxxxxxxxx.execute-api.us-east-1.amazonaws.com/v1"
    ```
    *(Note: The `PUBLIC_` prefix is **required** by SvelteKit to expose this variable to the browser).*

3.  **Install dependencies:**
    ```sh
    npm install
    ```

---

## 2.  Development

To run the local development server:

```sh
npm run dev
```


## 3. Production (Build & Run)

To run this project on a production server (like your EC2 instances), you cannot use `npm run dev`. You must first build the app and then run the resulting standalone Node.js server.

### 3.1. Setup (One-time)

This project is configured to use `@sveltejs/adapter-node`.

1.  **Install the adapter** (if not already present):
    ```bash
    npm install -D @sveltejs/adapter-node@latest
    ```

2.  **Verify `svelte.config.js`:**
    Ensure your `svelte.config.js` is set to use the node adapter:
    ```javascript
    import adapter from '@sveltejs/adapter-node';
    import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

    /** @type {import('@sveltejs/kit').Config} */
    const config = {
      preprocess: vitePreprocess(),
      kit: {
        adapter: adapter()
      }
    };
    export default config;
    ```

3.  **Add the `start` script to `package.json`:**
    For convenience, add a `start` script to your `package.json` file. This is the standard way to run a Node.js app in production.

    ```json
      "scripts": {
        "dev": "vite dev",
        "build": "vite build",
        "preview": "vite preview",
        "start": "node build/index.js"
      },
    ```

### 3.2. Build the App

Run the build command. This compiles all Svelte code into an optimized `build/` directory.

```bash
npm run build
```

### 3.3. Run the Server

Run the build command. This compiles all Svelte code into an optimized `build/` directory.

```bash
npm run build
```

This command will execute node build/index.js and start your production-ready server on http://localhost:3000.