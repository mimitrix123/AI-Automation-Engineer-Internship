# Mini Project — Week 2: AI Content Repurposer

Input a blog post URL, scrape the readable article content, use an AI API to generate a Twitter/X thread, LinkedIn post, and Instagram caption, then save everything to a formatted Word document.

## Workflow

1. Accept a blog URL from the command line.
2. Download the page with `requests`.
3. Extract readable paragraphs with BeautifulSoup.
4. Send the cleaned article to the OpenAI API.
5. Generate platform-specific content as JSON.
6. Save the outputs as a formatted `.docx` file.

## Setup

```bash
cd week2_content_repurposer
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Do not commit real API keys.

## Run

```bash
python content_repurposer.py "https://example.com/blog-post"
```

Generated documents are written to `outputs/` by default.

## Notes

The scraper removes common non-content elements such as navigation, scripts, forms, headers, footers, and sidebars. Some websites use JavaScript or anti-bot protections; those pages may require a browser-based scraper or an official content API instead.
