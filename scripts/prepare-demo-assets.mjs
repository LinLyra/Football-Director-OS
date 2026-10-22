import { copyFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const scenes = ['101', '068', '099'];
const destination = resolve('public/demo-scenes');
await mkdir(destination, { recursive: true });

for (const sequence of scenes) {
  const source = resolve(`cv_outputs/snmot-${sequence}/event-overlay.mp4`);
  const target = resolve(destination, `snmot-${sequence}.mp4`);
  await copyFile(source, target);
  console.log(`Prepared ${target}`);
}

console.log('Local real-video demo assets are ready. They remain Git-ignored.');
