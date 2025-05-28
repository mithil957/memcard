FROM golang:1.24-alpine

RUN apk add --no-cache git build-base

WORKDIR /app

RUN go install github.com/air-verse/air@latest

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o pocketbase_server main.go hooks.go

EXPOSE 8090

CMD ["air"] 
