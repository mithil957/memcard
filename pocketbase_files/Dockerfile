FROM golang:1.24-bookworm

RUN apt-get update && apt-get install -y git build-essential

WORKDIR /app

RUN go install github.com/air-verse/air@latest

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o pocketbase_server main.go hooks.go

EXPOSE 8090

CMD ["air"] 
