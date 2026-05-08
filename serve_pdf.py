import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from serve_web import refresh_output
from src.scraper import get_previous_week_range


class PDFReportHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in {'/', ''}:
            self.path = '/updates_pdf.html'
        return super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Refresh output.json and serve the PDF-style Azure updates report.'
    )
    parser.add_argument('--out', type=str, default='output.json', help='Output JSON path')
    parser.add_argument('--port', type=int, default=8001, help='HTTP server port')
    parser.add_argument('--bind', type=str, default='127.0.0.1', help='Address to bind')
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Refresh output.json before serving (slower startup).',
    )
    args = parser.parse_args()

    if args.refresh:
        start_date, end_date = get_previous_week_range()
        print(f'Refreshing data for week of {start_date} to {end_date}...')
        payload = refresh_output(args.out)
        print(
            f"Prepared {len(payload.get('azure_updates', []))} Azure updates for PDF-style report."
        )
    else:
        print('Using existing output.json (pass --refresh to fetch fresh data).')

    server = ThreadingHTTPServer((args.bind, args.port), PDFReportHandler)
    print(f'Serving PDF-style report at http://{args.bind}:{args.port}/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping server...')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
