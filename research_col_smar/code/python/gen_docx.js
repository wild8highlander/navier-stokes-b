/* gen_docx.js — build MONOGRAPH_{RU,EN}.docx per the docx skill.
 *
 * Usage: bun gen_docx.js ru|en
 *
 * Academic scene: R5 (Clean White) cover in its own section (margin 0,
 * 16838 exact wrapper, allNoBorders), front-matter section (TOC, Roman
 * numerals), body section (Arabic from 1). Headings use HeadingLevel;
 * tables use percentage widths, margins, tableHeader/cantSplit; images
 * keep aspect ratio. TOC gets the refresh hint and a PageBreak.
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, PageBreak, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  TableOfContents, SectionType, TableLayoutType, VerticalAlign,
} = require("docx");
const fs = require("fs");

const LANG = process.argv[2] || "en";
const data = JSON.parse(fs.readFileSync(`mg_content_${LANG}.json`, "utf8"));
const META = data.meta;
const RU = LANG === "ru";

const T = RU ? {
  tocTitle: "Оглавление",
  hint: "Примечание: оглавление построено на полях документа. После " +
    "редактирования обновите номера страниц: правый клик по оглавлению → " +
    "«Обновить поле».",
  edition: "Издание", author: "Автор", program: "Программа",
  date: "Дата", languages: "Языки реализации",
  languagesVal: "Python · C++ · Julia",
  programVal: "navier-stokes-b · research_col_smar",
  editionVal: RU ? "Русское" : "Русское",
  caption: "Рис.", tbl: "Таблица",
} : {
  tocTitle: "Table of Contents",
  hint: "Note: this Table of Contents is generated via field codes. To " +
    "ensure page number accuracy after editing, please right-click the " +
    "TOC and select \u201cUpdate Field.\u201d",
  edition: "Edition", author: "Author", program: "Program",
  date: "Date", languages: "Languages",
  languagesVal: "Python · C++ · Julia",
  programVal: "navier-stokes-b · research_col_smar",
  editionVal: "English",
  caption: "Fig.", tbl: "Table",
};

const FONT = { ascii: "Times New Roman", eastAsia: "Times New Roman", hAnsi: "Times New Roman" };
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB,
  insideHorizontal: NB, insideVertical: NB };

function estimateTextWidth(text, pt) {
  let width = 0;
  for (const ch of text) {
    const code = ch.codePointAt(0);
    const isWide = (code >= 0x4e00 && code <= 0x9fff) ||
      (code >= 0x3000 && code <= 0x303f);
    width += isWide ? pt * 20 : pt * 11;
  }
  return width;
}

function splitTitleLines(title, maxWidthTwips, pt) {
  const words = title.split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    const probe = cur ? cur + " " + w : w;
    if (estimateTextWidth(probe, pt) <= maxWidthTwips || !cur) {
      cur = probe;
    } else {
      lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  if (lines.length > 1 && lines[lines.length - 1].length <= 3) {
    const last = lines.pop();
    lines[lines.length - 1] += " " + last;
  }
  return lines;
}

function buildCover() {
  const contentW = 11906 - 1701 * 2;
  const titlePt = 30;
  const titleLines = splitTitleLines(META.title, contentW, titlePt);
  const subPt = 15;
  const subLines = splitTitleLines(META.subtitle, contentW - 600, subPt);

  const metaEntries = [
    [T.author, META.author],
    [T.program, T.programVal],
    [T.languages, T.languagesVal],
    [T.edition, T.editionVal],
    [T.date, META.footer_right],
  ];
  const metaRowH = 460;
  const titleTotalH = titleLines.length * (titlePt * 23 + 160);
  const subTotalH = subLines.length * (subPt * 23 + 120);
  const fixedH = 1100 + titleTotalH + subTotalH +
    metaEntries.length * metaRowH + 900 + 3 * 350;
  const safeH = 16838 - 1200;
  const remaining = Math.max(safeH - fixedH, 600);
  const topSpacing = Math.min(Math.floor(remaining * 0.30) + 1200, 4200);
  const midSpacing = Math.min(Math.floor(remaining * 0.16), 1800);
  const bottomSpacing = Math.max(
    Math.min(remaining - (topSpacing - 1200) - midSpacing, 5200), 800);

  const children = [];
  children.push(new Paragraph({ spacing: { before: topSpacing } }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: META.label.toUpperCase(),
      size: 20, color: "8B7E5A", font: FONT, characterSpacing: 60 })],
  }));
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: {
        after: i < titleLines.length - 1 ? 80 : 240,
        line: Math.ceil(titlePt * 23), lineRule: "atLeast",
      },
      children: [new TextRun({ text: titleLines[i], size: titlePt * 2,
        bold: true, font: FONT, color: "000000" })],
    }));
  }
  for (let i = 0; i < subLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i < subLines.length - 1 ? 60 : 200 },
      children: [new TextRun({ text: subLines[i], size: subPt * 2,
        italics: true, font: FONT, color: "444444" })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: midSpacing } }));

  const metaTable = new Table({
    width: { size: 62, type: WidthType.PERCENTAGE },
    alignment: AlignmentType.CENTER,
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: metaEntries.map(([label, value]) => new TableRow({
      children: [
        new TableCell({
          width: { size: 38, type: WidthType.PERCENTAGE },
          borders: noBorders,
          margins: { left: 0, right: 0 },
          children: [new Paragraph({
            alignment: AlignmentType.LEFT,
            spacing: { before: 40, after: 40, line: 320 },
            children: [new TextRun({ text: label + ":", size: 22,
              font: FONT, color: "555555" })],
          })],
        }),
        new TableCell({
          width: { size: 62, type: WidthType.PERCENTAGE },
          borders: { top: NB, left: NB, right: NB,
            bottom: { style: BorderStyle.SINGLE, size: 4, color: "000000" } },
          margins: { left: 80, right: 0 },
          children: [new Paragraph({
            alignment: AlignmentType.LEFT,
            spacing: { before: 40, after: 40, line: 320 },
            children: [new TextRun({ text: value, size: 22, font: FONT,
              color: "000000" })],
          })],
        }),
      ],
    })),
  });
  children.push(metaTable);
  children.push(new Paragraph({ spacing: { before: bottomSpacing } }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: META.footer_left + " · " +
      META.footer_right, size: 22, font: FONT, color: "404040" })],
  }));

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "FFFFFF" },
        borders: noBorders, verticalAlign: VerticalAlign.TOP,
        margins: { left: 1701, right: 1701 },
        children,
      })],
    })],
  })];
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 480, after: 240, line: 360 },
    children: [new TextRun({ text, bold: true, size: 32, font: FONT,
      color: "000000" })],
  });
}
function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 320, after: 160, line: 360 },
    children: [new TextRun({ text, bold: true, size: 28, font: FONT,
      color: "000000" })],
  });
}
function body(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: RU ? 709 : 480 },
    spacing: { line: 360, after: 80 },
    children: [new TextRun({ text, size: 24, font: FONT, color: "000000" })],
  });
}
function refItem(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    indent: { left: 480, hanging: 480 },
    spacing: { line: 320, after: 60 },
    children: [new TextRun({ text, size: 21, font: FONT, color: "000000" })],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 },
    children: [new TextRun({ text, size: 20, italics: true, font: FONT,
      color: "555555" })],
  });
}
function centeredImage(path, wPx, hPx, maxWPt) {
  const buf = fs.readFileSync(path);
  const ratio = hPx / wPx;
  const wPt = Math.min(maxWPt, 460);
  const hPt = Math.round(wPt * ratio);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 40 },
    children: [new ImageRun({ data: buf, type: "png",
      transformation: { width: wPt * 1.333, height: hPt * 1.333 } })],
  });
}

function buildBody() {
  const out = [];
  let figNo = 0;
  for (const b of data.blocks) {
    if (b.t === "h1") out.push(heading1(b.text));
    else if (b.t === "h2") out.push(heading2(b.text));
    else if (b.t === "p") out.push(body(b.text));
    else if (b.t === "ref") out.push(refItem(b.text));
    else if (b.t === "formula") {
      out.push(centeredImage(b.path, b.w, b.h, 300));
      out.push(new Paragraph({
        alignment: AlignmentType.RIGHT, spacing: { after: 120 },
        children: [new TextRun({ text: b.eqno, size: 20, font: FONT,
          color: "777777" })],
      }));
    } else if (b.t === "fig") {
      figNo += 1;
      out.push(centeredImage(b.path, b.w, b.h, 440));
      out.push(caption(b.caption));
    } else if (b.t === "table") {
      const ncol = b.headers.length;
      const headerRow = new TableRow({
        tableHeader: true, cantSplit: true,
        children: b.headers.map((h) => new TableCell({
          width: { size: 100 / ncol, type: WidthType.PERCENTAGE },
          shading: { type: ShadingType.CLEAR, fill: "4e4732" },
          margins: { left: 100, right: 100, top: 60, bottom: 60 },
          children: [new Paragraph({
            children: [new TextRun({ text: h, bold: true, size: 19,
              font: FONT, color: "FFFFFF" })],
          })],
        })),
      });
      const rows = [headerRow];
      b.rows.forEach((r, i) => {
        rows.push(new TableRow({
          cantSplit: true,
          children: r.map((cell) => new TableCell({
            width: { size: 100 / ncol, type: WidthType.PERCENTAGE },
            shading: { type: ShadingType.CLEAR,
              fill: i % 2 === 1 ? "ededeb" : "FFFFFF" },
            margins: { left: 100, right: 100, top: 50, bottom: 50 },
            children: [new Paragraph({
              children: [new TextRun({ text: String(cell), size: 19,
                font: FONT, color: "000000" })],
            })],
          })),
        }));
      });
      const table = new Table({
        width: { size: 98, type: WidthType.PERCENTAGE },
        alignment: AlignmentType.CENTER,
        borders: {
          top: { style: BorderStyle.SINGLE, size: 2, color: "c5bfac" },
          bottom: { style: BorderStyle.SINGLE, size: 2, color: "c5bfac" },
          left: NB, right: NB,
          insideHorizontal: { style: BorderStyle.SINGLE, size: 1,
            color: "d8d5cd" },
          insideVertical: NB,
        },
        rows,
      });
      out.push(new Paragraph({ spacing: { before: 160 } }));
      out.push(table);
      out.push(caption(b.caption));
    }
  }
  return out;
}

function headerFooter() {
  return {
    headers: { default: new Header({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { bottom: { style: BorderStyle.SINGLE, size: 2,
        color: "c5bfac", space: 4 } },
      children: [new TextRun({ text: META.title, size: 16, italics: true,
        font: FONT, color: "888888" })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18,
        font: FONT, color: "777777" })],
    })] }) },
  };
}

const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417,
  header: 850, footer: 992 };

const doc = new Document({
  creator: "navier-stokes-b research program",
  title: META.title,
  description: META.subtitle,
  styles: {
    default: {
      document: {
        run: { font: FONT, size: 24, color: "000000" },
        paragraph: { spacing: { line: 360 } },
      },
      heading1: {
        run: { font: FONT, size: 32, bold: true, color: "000000" },
        paragraph: { spacing: { before: 480, after: 240, line: 360 },
          outlineLevel: 0 },
      },
      heading2: {
        run: { font: FONT, size: 28, bold: true, color: "000000" },
        paragraph: { spacing: { before: 320, after: 160, line: 360 },
          outlineLevel: 1 },
      },
    },
  },
  sections: [
    { // cover — margin 0, no footer
      properties: { page: { size: pgSize,
        margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCover(),
    },
    { // front matter: TOC — Roman numerals
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin,
          pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } },
      },
      ...headerFooter(),
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 360 },
          children: [new TextRun({ text: T.tocTitle, bold: true, size: 32,
            font: FONT, color: "000000" })],
        }),
        new TableOfContents("Table of Contents", {
          hyperlink: true, headingStyleRange: "1-2",
        }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({ text: T.hint, italics: true, size: 18,
            font: FONT, color: "888888" })],
        }),
        new Paragraph({ children: [new PageBreak()] }),
      ],
    },
    { // body — Arabic from 1
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin,
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      ...headerFooter(),
      children: buildBody(),
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = `../../monograph/MONOGRAPH_${LANG.toUpperCase()}.docx`;
  fs.writeFileSync(out, buf);
  console.log(`[docx] wrote ${out} (${Math.round(buf.length / 1024)} KB)`);
});
