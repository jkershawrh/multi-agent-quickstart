import { readFile, readdir } from 'node:fs/promises'
import { join } from 'node:path'

const dist = new URL('../dist/', import.meta.url)
const html = await readFile(new URL('index.html', dist), 'utf8')
if (/fonts\.googleapis|fonts\.gstatic|https?:\/\/.*\.(woff|otf|ttf)/i.test(html)) {
  throw new Error('Build references remote font assets.')
}

const fonts = await readdir(new URL('fonts/', dist))
if (!fonts.some((name) => name.includes('RedHatDisplay')) || !fonts.some((name) => name.includes('RedHatText'))) {
  throw new Error('Local Red Hat fonts are missing from the production build.')
}

const logos = await readdir(new URL('logos/', dist))
for (const required of ['redhat.svg', 'intel.png']) {
  if (!logos.includes(required)) throw new Error(`Missing offline logo: ${required}`)
}

console.log(`Offline assets verified in ${join(dist.pathname)}.`)
