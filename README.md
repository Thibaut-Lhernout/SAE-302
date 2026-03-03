# T1b021 research

Client/server document search for SAE 302.
The server indexes text, HTML, PDF and Excel files in the `documents/` folder, and the graphical client sends queries and displays the results.[2]

## Project structure


```text
SAE32/
├── documents/           # Documents to be searched (.txt, .html, .pdf, .xlsx, ...)
├── source/
│   ├── client_gui.py    # Graphical user interface (Tkinter)
│   ├── server.py        # TCP server (socket + threads)
│   └── search_engine.py # Search engine (TXT, HTML, PDF, XLSX)
├── requirements.txt
└── README.md
```

## Installation and run

```
1. Create a virtual environment (recommended):
```

   python3 -m venv .venv  
   source .venv/bin/activate[2]

```
2. Install Python dependencies:
```

   pip install -r requirements.txt[2]
   
```
3. Put all documents to be searched into the `documents/` folder.[2]
```

```
4. Start the server:
```

   cd source  
   python server.py[2]

```
5. Start the GUI client in another terminal:
```

   cd source  
   python client_gui.py[2]

## Features

- Graphical user interface (Tkinter) to enter queries, enable regex mode, and select which file types to search (`.txt`, `.html`, `.pdf`, `.xlsx`).[2]
- TCP server with multi-client support using threads, listening on `127.0.0.1:65432`.[2]
- Search engine supporting:
  - Simple keyword search.[2]
  - Advanced search with logical operators `AND` and `OR` when regex mode is disabled.[2]
  - Regular expression search when `regex_mode` is enabled.[2]
- Supported file formats:
  - TXT and HTML: text is scanned line by line with line numbers reported.[2]
  - PDF: text is extracted page by page with page numbers reported.[2]
  - Excel (XLS/XLSX): all sheets and cells are scanned with sheet name and cell coordinates reported.[2]
- For each match, the client displays:
  - File name, file type, and a location string (line, page, or cell).[2]
  - A short text snippet providing context around the match.[2]

## Query examples

- Simple search: `programme`[2]
- Logical AND: `programme AND fichier`[2]
- Logical OR: `programme OR texte`[2]
- Regex search (with `regex_mode` enabled): `progr.*` ou `fich(ier|iers)`  [2]

