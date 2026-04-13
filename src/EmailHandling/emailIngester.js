import Imap from "imap";
import { simpleParser } from "mailparser";
import fs from "fs";
import path from "path";

// Cache of URLs already processed
const processedUrls = new Set();

function readInbox() {
    // Connect to email inbox, search for unseen emails, extract text and parse to process function
    const imap = new Imap({
    user: process.env.EMAIL_USER,
    password: process.env.EMAIL_PASS,
    host: "imap.gmail.com",
    port: 993,
    tls: true,
    tlsOptions: { rejectUnauthorized: false }
    });

    imap.once("ready", () => {
    imap.openBox("INBOX", false, () => {
        imap.search(["UNSEEN"], (err, results) => {

        if (!results || results.length === 0) {
            console.log("No new emails");
            return;
            }  
        const fetch = imap.fetch(results, { bodies: "" });

        fetch.on("message", (msg) => {

            msg.on("attributes", (attrs) => {
                const uid = attrs.uid;
                imap.addFlags(uid, ["\\Seen"], () => {});
            });
            msg.on("body", async (stream) => {
            const parsed = await simpleParser(stream);

            console.log(parsed.subject);
            console.log(parsed.text);
            processEmail(parsed.text);
            });
        });
        });
    });
    });

    imap.connect();
}

// extract the URL's from the email text
function extractGovUkUrls(text) {
  const matches = text.match(/https:\/\/www\.gov\.uk\/[^\s]+/g);
  return matches || [];
}

// process the email text: extract URL, scrape page, extract update, validate and log
async function processEmail(emailText) {
    const urls = extractGovUkUrls(emailText);

    if (urls.length === 0) {
        console.log("No gov.uk URLs found");
        return;
    }

    for (const url of urls) {
        // Skip if we've already processed this URL
        if (processedUrls.has(url)) {
        console.log("Already processed:", url);
        continue;
        }

        processedUrls.add(url);

        try {

        console.log("Processing:", url);

        const pageText = await scrapePage(url); // scrape page and check for pdfs

        const extracted = await extractUpdateFromPage(pageText, url); // send to LLM for structured extraction
        // If not relevant, skip    
        if (!extracted.relevant) {
            console.log("Page not relevant, skipping:", url);
            return;
        }
        // Validate the extracted data against our schema
        const validated = UpdateSchema.parse(extracted);

        console.log("Structured Update:");
        console.log(validated);

        // Export to txt
        exportToTxt(validated, pageText);
        

        } catch (err) {
        console.error("Failed for URL:", url);
        console.error(err);
        }
    }
}

const OUTPUT_FOLDER = path.resolve("./Outputs");

function sanitizeFileName(name) {
  return name.replace(/[<>:"/\\|?*]/g, "").replace(/\s+/g, "_");
}
// this function takes the structured data and saves it as a .txt file in the Outputs folder, using the title as the filename
function exportToTxt(structuredData, fullPageText) {
  const fileName = `${sanitizeFileName(structuredData.title)}_${Date.now()}.txt`;
  const filePath = path.join(OUTPUT_FOLDER, fileName);

  // Convert JSON to a human-readable string
  const content = `
    Title: ${structuredData.title}
    Organisation: ${structuredData.organisation}
    Policy Area: ${structuredData.policy_area}
    Summary: ${structuredData.summary}
    Key Changes: ${structuredData.key_changes}
    URL: ${structuredData.url}
    ${fullPageText}
    `;

    fs.writeFileSync(filePath, content, "utf-8");
    console.log("Saved file:", filePath);
}

// Define your main function
async function main() {
  console.log("Starting email ingestion pipeline...");

  // Example: call the IMAP connect/setup logic
  readInbox();
}

main();