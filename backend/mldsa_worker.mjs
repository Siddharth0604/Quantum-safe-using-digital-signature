import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js';

const CONTEXT = new TextEncoder().encode('QuantumSafe file signature v1');
const input = await new Promise((resolve, reject) => {
  const chunks = [];
  process.stdin.on('data', chunk => chunks.push(chunk));
  process.stdin.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  process.stdin.on('error', reject);
});

try {
  const request = JSON.parse(input);
  const decode = value => new Uint8Array(Buffer.from(value, 'base64'));
  const encode = value => Buffer.from(value).toString('base64');
  let response;
  if (request.operation === 'generate') {
    const keys = ml_dsa65.keygen();
    response = { publicKey: encode(keys.publicKey), secretKey: encode(keys.secretKey) };
  } else if (request.operation === 'sign') {
    const signature = ml_dsa65.sign(decode(request.message), decode(request.secretKey), { context: CONTEXT });
    response = { signature: encode(signature) };
  } else if (request.operation === 'verify') {
    let valid = false;
    try {
      valid = ml_dsa65.verify(decode(request.signature), decode(request.message), decode(request.publicKey), { context: CONTEXT });
    } catch {
      valid = false;
    }
    response = { valid };
  } else {
    throw new Error('Unsupported operation');
  }
  process.stdout.write(JSON.stringify(response));
} catch {
  // Keep error details and request material out of stdout/stderr.
  process.stderr.write('ML-DSA operation failed.');
  process.exitCode = 1;
}
