"""atq server entry point."""
import argparse
from atq import atqserver

NUM_WORKERS_DEFAULT = 4

def main():
    """Main function of the module."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-H', '--host', dest='host', type=str, required=True,
                        help='set server host')
    parser.add_argument('-p', '--port', dest='port', type=int, required=True,
                        help='set server port')
    parser.add_argument('-w', '--workers', dest='num_workers', type=int,
                        default=NUM_WORKERS_DEFAULT,
                        help='max number of workers')
    args = parser.parse_args()
    worker_server = atqserver.QServer.create(
        args.host, args.port, args.num_workers)
    try:
        worker_server.run_forever()
    except KeyboardInterrupt:
        worker_server.shutdown()


if __name__ == '__main__':
    main()
