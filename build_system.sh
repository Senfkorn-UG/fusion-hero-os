#!/bin/bash
# Master Build Skript
sudo apt-get update && sudo apt-get install -y dotnet-sdk-9.0 julia git docker.io protobuf-compiler
git clone https://github.com/95guknow/dashboard heroic-core
cd heroic-core
dotnet publish controller_csharp/HeroicCore.csproj -c Release -o ./bin/controller
julia -e 'using Pkg; Pkg.add(["LinearAlgebra", "JSON", "HTTP"]); Pkg.precompile();'
protoc --csharp_out=./controller_csharp/proto proto/heroic_core.proto
docker build -t heroic-core/main-engine .
sudo cp infrastructure/heroic_daemon.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable heroic-core && sudo systemctl restart heroic-core
