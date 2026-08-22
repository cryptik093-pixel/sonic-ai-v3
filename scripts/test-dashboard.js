const http = require('http');

async function check() {
  const url = 'http://127.0.0.1:8000/dashboard';
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      const { statusCode } = res;
      if (statusCode !== 200) return reject(new Error('Status ' + statusCode));
      let raw = '';
      res.on('data', (c) => (raw += c));
      res.on('end', () => {
        try {
          const j = JSON.parse(raw);
          if (typeof j.projects === 'number' && typeof j.assets === 'number' && typeof j.ai_jobs === 'number') {
            resolve(j);
          } else {
            reject(new Error('Unexpected payload'));
          }
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

check().then((j) => {
  console.log('OK', j);
  process.exit(0);
}).catch((e) => {
  console.error('ERR', e.message || e);
  process.exit(2);
});
