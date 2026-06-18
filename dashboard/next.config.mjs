/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export so the dashboard deploys to GitHub Pages / Vercel with no server.
  output: "export",
  images: { unoptimized: true },
  // Set NEXT_PUBLIC_BASE_PATH=/projectsf when hosting under a GitHub Pages subpath.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  trailingSlash: true,
};

export default nextConfig;
