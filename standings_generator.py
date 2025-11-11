import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "TABLAGRUPOBclausura2025.xlsx"
OUTPUT_FILE = "standings.html"

CATEGORIES = ["TERCERA", "SEGUNDA", "INFANTILES", "SENIOR", "PRIMERA"]

def find_tables(df):
    """Return dict: {category_name : sub_dataframe}"""
    blocks = {}
    rows = df.iloc[:, 0].astype(str).str.upper()

    # locate indices where category rows begin
    start_indices = []
    for idx, v in rows.items():
        if v in CATEGORIES:
            start_indices.append((idx, v))

    # add last possible ending
    start_indices.append((len(df), None))

    # slice blocks
    for i in range(len(start_indices) - 1):
        start, name = start_indices[i]
        end = start_indices[i + 1][0]

        sub = df.iloc[start+1:end].copy()

        # remove blank lines
        sub = sub.dropna(how="all")
        if len(sub) == 0:
            continue

        # rename first column to TEAM
        sub.columns = [str(c).strip().upper() for c in sub.columns]
        sub.rename(columns={sub.columns[0]: "TEAM"}, inplace=True)

        blocks[name] = sub

    return blocks


def parse_match(val):
    val = val.strip()
    if isinstance(val, str):
        try:
            a, b = re.split(r"\s*-\s*", val)
            return int(float(a)), int(float(b))
        except:
            pass
    return None


def compute_table(df, cat):
    match_cols = [c for c in df.columns if re.match(r"^\d+$", str(c))]
    results = []

    for _, row in df.iterrows():
        team = row["TEAM"]
        pj = 0
        gf = 0
        gc = 0
        pts = 0

        v,counter = '', 0
        for col in match_cols:
            v += str(row[col])
            if counter==1 and  str(row[col])!='-': 
                ptsori = v[:-len(str(row[col]))]
                break
            if (isinstance(v, str) and v.upper() == "LIBRE") or v == 'nan' or (counter==0 and v=='-'):
                v,counter = '', 0
                continue
            counter += 1
            if counter < 3: continue
            if counter > 3:
                print('Error',team,v)
                exit(1)
            parsed = parse_match(v)
            if parsed:
                g_for, g_con = parsed
                pj += 1
                gf += g_for
                gc += g_con
                if g_for > g_con:
                    pts += 3
                elif g_for == g_con:
                    pts += 1
            v,counter = '', 0

        dg = gf - gc
        if INPUT_FILE == "TABLAGRUPOBclausura2025.xlsx":
            if cat == 'TERCERA' and (team == ' CAMINO VIEJO' or team == 'TRICOLOR'):pj+=1
            if cat == 'SEGUNDA' and team == 'JUVENTUD': pts +=3
            if cat == 'PRIMERA':
                if team == 'JUVENTUD': pts+=3; pj +=1
                if team == 'CAMINO VIEJO': pj +=1

        if int(float(ptsori)) != pts:
            print(f'Warning Serie: {cat} Team: {team} does not match pts {int(float(ptsori))} vs {pts}')
        results.append([team, pj, dg, pts, gf, gc])

    out = pd.DataFrame(results, columns=["Team", "PJ", "DG", "Pts", "GF", "GC"])
    out = out.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
    out.insert(0, "Pos", out.index + 1)
    return out


def build_html(tables_dict):
    html = """
<section class="standings">
  <h2>Tablas de Posiciones Grupo B</h2>
  <div class="tables-container">
"""

    for category, df in tables_dict.items():
        html += f"""
    <div class="table-box">
      <h3>{category.capitalize()}</h3>
      <table>
        <tr><th>Pos</th><th>Team</th><th>PJ</th><th>DG</th><th>Pts</th></tr>
"""
        for _, row in df.iterrows():
            highlight = f'class="pos-{row.Pos}"' if row.Pos <= 4 else ""
            html += f"""        <tr {highlight}>
          <td>{row.Pos}</td><td>{row.Team}</td><td>{row.PJ}</td><td>{row.DG}</td><td>{row.Pts}</td>
        </tr>
"""

        html += """      </table>
    </div>
"""

    html += """
  </div>
</section>

<div id="table-overlay" onclick="this.style.display='none'">
  <div id="table-popup"></div>
</div>

<script>
  document.querySelectorAll('.table-box table').forEach(table => {
    table.addEventListener('click', () => {
      const overlay = document.getElementById('table-overlay');
      const popup = document.getElementById('table-popup');
      popup.innerHTML = table.outerHTML;
      overlay.style.display = 'flex';
    });
  });
</script>
"""

    return html


def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=0, header=None)

    tables_raw = find_tables(df)

    final_tables = {}
    for cat, block in tables_raw.items():
        try:
            tab = compute_table(block, cat)
            final_tables[cat] = tab.sort_values('Pts',ascending=False)
        except Exception as e:
            print(f"Error processing {cat}: {e}")

    html = build_html(final_tables)
    Path(OUTPUT_FILE).write_text(html, encoding="utf-8")
    print(f"\n✅ Created {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
