## ChitChat

**Category**: pwn

**Author**: UDP

**Description**: Talk is cheap.

**Public Files**: out/ (remember to build docker)

**Solution**: scripts/

**Flag**: bwctf{681c100981fe527a96bf83d1c84e3dbd}

**Notes**: To build, run `docker build . -t chitchatbuild && docker run --rm -it -v $(pwd):/app/ chitchatbuild sh -c "cd /app/src/ && make"`
