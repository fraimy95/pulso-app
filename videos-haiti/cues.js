const { chromium } = require('playwright'); const path=require('path'); const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+path.resolve(process.argv[2]));
fs.writeFileSync(process.argv[3],JSON.stringify(await p.evaluate(()=>window.CUES)));await b.close();})();
