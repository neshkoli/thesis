export function parseCsv(text) {
  const records = [];
  let field = "";
  let row = [];
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
      continue;
    }

    if (ch === ",") {
      row.push(field);
      field = "";
      continue;
    }

    if (ch === "\n") {
      if (field.endsWith("\r")) field = field.slice(0, -1);
      row.push(field);
      field = "";
      if (row.some((cell) => cell !== "")) records.push(row);
      row = [];
      continue;
    }

    field += ch;
  }

  if (field.endsWith("\r")) field = field.slice(0, -1);
  if (field !== "" || row.length > 0) {
    row.push(field);
    if (row.some((cell) => cell !== "")) records.push(row);
  }

  if (records.length === 0) return [];

  const headers = records[0];
  return records.slice(1).map((cells) => {
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = cells[index] ?? "";
    });
    return obj;
  });
}

export function dataRows(rows) {
  return rows.filter((row) => String(row.snippet ?? "").trim() !== "");
}
