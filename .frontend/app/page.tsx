import React from 'react'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8">Welcome to Llama Agent</h1>
        <p className="text-xl mb-4">
          This is a boilerplate project featuring:
        </p>
        <ul className="list-disc list-inside space-y-2">
          <li>Next.js Frontend with TypeScript</li>
          <li>FastAPI Backend</li>
          <li>PDM for Python dependency management</li>
          <li>PNPM for Node.js dependency management</li>
        </ul>
      </div>
    </main>
  )
}
