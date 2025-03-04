# Custom Local RAG[WIP]

## Description
This repo contains the necessary configuration to deploy a minimal local RAG locally, I'm using it for learning purposes so no production grade code to be found here.

My use case was to parse bank statements coming from 2 different companies(BBVA, Galicia) and store relevant information to be used with RAG in order for me to quickly get my expenses, unfortunately parsing bank statements PDFs which are 100% text and contain "tables" but not really as its just text lines separated by spaces was ugly. However I will include some code on getting text from PDFs which are easier to parse for general purpose RAG testing.

Why running a local RAG system?
Well I didn't want any AI company having my financial info, also posed a cool learning challenge

## Prerequisites
I'm using [Llama.cpp](https://github.com/ggml-org/llama.cpp) for LLM inferencing and embedding to be as lightweight as I could get. In order to run it we first need our favorite LLM model either already quantized or to be quantized by you in the GGUF file format.
Reference on how to do this [here](https://github.com/ggml-org/llama.cpp?tab=readme-ov-file#obtaining-and-quantizing-models)

An alternative is to use [ollama](https://ollama.com/) to download model files, just download the CLI and run the following command:

```bash
ollama pull model:tag
```

This will pull the model into `~/.ollama/models` for Linux or `C:\Users\User\.ollama` for Windows, check the manifest file to get which of the blob files corresponds to the model, also check that the file format is correct.

In my particular case I'm using this model `deepseek-R1-14b-Q4_K_m`, the GGUF file can be downloaded [here](https://ollama.com/library/deepseek-r1:14b). I'm using a distilled version of the model but works alright in my gaming PC, I'll detail my specs below.

## My PC specs
```
Operating system: Microsoft Windows 11 Pro, Version 10.0.26100
CPU: 12th Gen Intel(R) Core(TM) i7-12700K
RAM: 32.0 GB
Storage: SSD - 931.5 GB

Graphics card
GPU processor: NVIDIA GeForce RTX 3080 Ti
Direct3D feature level: 12_1
CUDA cores: 10240
Graphics clock: 1665 MHz
Resizable bar: No
Memory data rate: 19.00 Gbps
Memory interface: 384-bit
Memory bandwidth: 912.096 GB/s
Total available graphics memory: 28542 MB
Dedicated video memory: 12288 MB GDDR6X
System video memory: 0 MB
Shared system memory: 16254 MB
Video BIOS version: 94.02.71.40.df
IRQ: Not used
Bus: PCI Express x16 Gen4
```

I'm also using WSL and CUDA to offload layers to my GPU, if your setup is similar then you'll need the NVIDIA container toolkit and the CUDA toolkit installed on WSL. Check the [documentation](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) on set this up.

## How to use
Every component in the system is configured in the [docker compose](./docker-compose.yml) file, you can take a look at each one there. Below is a brief description of each. 
Take into consideration that each use case might be different so this might not fit your particular needs, also the logic is minimal to get things running.

### Chatter
This service uses the Llamma.cpp server component for LLM inferencing with any model you would like to use and an OpenAI API endpoint, just change the mount path to your local directory and run. For more info in configuring the server take a look [here](https://github.com/ggml-org/llama.cpp?tab=readme-ov-file#llama-server) 

### Loader
The purpose of this script is to populate the vector DB by reading, parsing, embedding and uploading data into Qdrant. This part will need the most work for any custom RAG, right now it fits my use case.

### Qdrant
Service hosting [Qdrant](https://qdrant.tech/) vector DB

### Embedder
Simple embedding server endpoint using Llama.cpp, the model I'm currently using is very lightweight as it was created for this task. `nomic-embed-text-latest`

### Summary analyzer
Simple fast api endpoint to interface with the embedder and chatter services

## TODOs
- Boilerplate code for general PDF RAG
- Parse LLM response
