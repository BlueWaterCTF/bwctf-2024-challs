FROM golang

WORKDIR /app

COPY ./build/readflag.c /readflag.c
RUN gcc -o /readflag /readflag.c

COPY ./build/go.mod ./build/go.sum ./

COPY ./build ./

# RUN CGO_ENABLED=1 GOOS=linux go build -o /app/sandevistan /app/main.go

COPY ./flag /flag

RUN chown 0:0 /readflag /flag
RUN chmod 400 /flag
RUN chmod +x /readflag
RUN chmod +s /readflag

EXPOSE 8080

CMD ["/app/sandevistan"]