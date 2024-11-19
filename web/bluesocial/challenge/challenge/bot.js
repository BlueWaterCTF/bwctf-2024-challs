const puppeteer = require("puppeteer");
const crypto = require("crypto");

const PORT = process.env.PORT || 1337;
const SITE = process.env.SITE || `localhost:{PORT}`

const FLAG = process.env.FLAG || "bwctf{test_flag}";
const FLAG_REGEX = /^bwctf{[a-z_]+}$/;

const sleep = async (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const visit = (url) => {
    return new Promise(async (resolve, reject) => {
        if (!FLAG_REGEX.test(FLAG)) {
            return reject(new Error("error: flag does not match flag regex, contact an admin if this is on remote"));
        }

        let browser, context, page;
        try {
            browser = await puppeteer.launch({
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--js-flags=--noexpose_wasm,--jitless' // this is a web chall :)
                ],
                dumpio: true,
                pipe: true,
                executablePath: process.env.PUPPETEER_EXEC_PATH
            });
    
            // incognito btw
            context = await browser.createBrowserContext();

          } catch (err) {
            console.error(err);
            return reject(new Error("error: setup failed, if this happens consistently on remote contact an admin"));
        }
        resolve("the admin will visit your URL soon");
        try {
            page = await context.newPage();

            await page.setCookie({
                name: 'flag',
                value: FLAG,
                domain: SITE, // to remove the http://
                httpOnly: false
            });

            await page.goto(url, { waitUntil: "domcontentloaded", timeout: 5000 });
            await sleep(10_000);
        } catch (err) {
            console.error(err);
        }

        await browser.close();
    });
};

module.exports = { visit };
