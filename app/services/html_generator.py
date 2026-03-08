from typing import List, Dict
from app.models import Word


def generate_tutorial_html(words: List[Word], title: str) -> str:
    """
    Generate a self-contained HTML page with Buddhist/traditional aesthetic.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="bo">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Tibetan Learning Tutorial</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Serif Tibetan', 'Microsoft Himalaya', serif;
            background: linear-gradient(135deg, #FDF5E6 0%, #FAF0E6 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 50px;
            padding: 30px;
            background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(139, 0, 0, 0.3);
        }}

        header h1 {{
            color: #FFD700;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
        }}

        header p {{
            color: #FDF5E6;
            font-size: 1.1em;
        }}

        .ornament {{
            text-align: center;
            font-size: 2em;
            color: #DAA520;
            margin: 20px 0;
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 15px;
            background: transparent;
        }}

        thead tr {{
            background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%);
        }}

        thead th {{
            padding: 20px 15px;
            text-align: center;
            color: #FFF;
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        thead th:first-child {{
            border-radius: 10px 0 0 10px;
        }}

        thead th:last-child {{
            border-radius: 0 10px 10px 0;
        }}

        tbody tr {{
            background: #FFF;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        tbody tr:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}

        tbody td {{
            padding: 25px 15px;
            text-align: center;
            border-top: 1px solid #EEE;
            border-bottom: 1px solid #EEE;
        }}

        tbody td:first-child {{
            border-left: 4px solid #8B0000;
            border-radius: 10px 0 0 10px;
        }}

        tbody td:last-child {{
            border-right: 1px solid #EEE;
            border-radius: 0 10px 10px 0;
        }}

        .tibetan {{
            font-size: 2.2em;
            color: #8B0000;
            font-weight: bold;
        }}

        .phonetic {{
            font-family: 'Georgia', serif;
            font-size: 1.1em;
            color: #666;
            font-style: italic;
        }}

        .chinese {{
            font-size: 1.3em;
            color: #333;
        }}

        .english {{
            font-family: 'Georgia', serif;
            font-size: 1.1em;
            color: #555;
        }}

        .word-number {{
            display: inline-block;
            background: #8B0000;
            color: #FFD700;
            width: 30px;
            height: 30px;
            line-height: 30px;
            border-radius: 50%;
            font-size: 0.8em;
            margin-bottom: 10px;
        }}

        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            color: #8B0000;
            font-size: 0.9em;
        }}

        footer .dharma-wheel {{
            font-size: 2em;
            margin-bottom: 15px;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8em;
            }}

            table {{
                display: block;
                overflow-x: auto;
            }}

            .tibetan {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>༄ {title} ༄</h1>
            <p>Tibetan Language Learning Tutorial</p>
        </header>

        <div class="ornament">❀ ❁ ❀</div>

        <table>
            <thead>
                <tr>
                    <th>Tibetan</th>
                    <th>Phonetic</th>
                    <th>中文</th>
                    <th>English</th>
                </tr>
            </thead>
            <tbody>
"""

    for word in words:
        phonetic = word.phonetic or "-"
        chinese = word.chinese or "-"
        english = word.english or "-"
        pos = f"（{word.pos}）" if word.pos else ""

        html_content += f"""                <tr>
                    <td>
                        <div class="word-number">{word.word_order + 1}</div>
                        <div class="tibetan">{word.tibetan_word}</div>
                    </td>
                    <td class="phonetic">{phonetic}</td>
                    <td class="chinese">{chinese}{pos}</td>
                    <td class="english">{english}</td>
                </tr>
"""

    html_content += """            </tbody>
        </table>

        <footer>
            <div class="dharma-wheel">☸</div>
            <p>Generated by Tibetan Learning Tutorial Generator</p>
            <p>May all beings benefit from this learning material.</p>
        </footer>
    </div>
</body>
</html>"""

    return html_content
