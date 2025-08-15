# Clipipe

Pronunciation: _Clip + Pipe_

`clipipe` is a command-line tool that allows you to pipe the output of one command to another machine. It works behind NAT and is designed to be used in shell pipelines, where the output of one command is passed as input to another command.

## How Does It Work?

`clipipe` reads data from standard input (stdin) and sends it to the server (also open source) via HTTPS. The server responds with a human-readable code, which you can share with others. The server stores the data in a Redis database with an expiration time. On another machine, you can use `clipipe` to retrieve the data for the given code from the server and output it to standard output (stdout).

## Installation

You can install the CLI tool from PyPI:

```bash
pipx install clipipe
```

Or use `uv`:

```bash
uvx install clipipe
```

## User Guide

### Sending Data

Pipe any data to the server and receive a retrieval code:

```bash
echo "Hello World" | clipipe send
cat file.txt | clipipe send
tar cz file.txt | clipipe send
clipipe send < data.json
```

The server will respond with a code, for example: `bafilo42`. You can share this code with anyone who needs to retrieve the data.

### Retrieving Data

Use the code to fetch the data from the server:

```bash
clipipe receive bafilo42
clipipe receive bafilo42 > output.txt
clipipe receive bafilo42 | tar xz
```

### Checking Server Status

Check if the server is online:

```bash
clipipe status
```

### Custom Server

By default, `clipipe` connects to `https://clipipe.io`. To use a different server, set the `CLIPIPE_SERVER` environment variable or use the `--server` option:

```bash
export CLIPIPE_SERVER="https://your-clipipe-server.com"
clipipe send < file.txt
```

Or:

```bash
clipipe --server https://your-clipipe-server.com receive bafilo42
```

## Features

- Simple, human-readable codes for data retrieval.
- Works behind NAT and firewalls.
- Designed for shell pipelines to work with other tools.
- Open source server and client.
- Data stored temporarily with automatic expiration.

## Roadmap

- [ ] Built-in end-to-end encryption.
- [ ] Add HTTP streaming.
- [ ] Peer-to-peer support via WebRTC.

## License

MIT
