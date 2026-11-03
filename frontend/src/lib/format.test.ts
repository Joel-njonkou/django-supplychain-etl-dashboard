import { describe, expect, it } from "vitest";

import { formater } from "@/lib/format";

const espacesNormaux = (texte: string) => texte.replace(/\s/g, " ");

describe("formater", () => {
  it("affiche un tiret quand la valeur est absente, jamais 0", () => {
    expect(formater(null, "pct")).toBe("—");
    expect(formater(undefined, "euros")).toBe("—");
  });

  it("formate un taux en pourcentage à la française", () => {
    expect(espacesNormaux(formater(0.4269, "pct"))).toBe("42,7 %");
  });

  it("sépare les milliers et utilise la virgule décimale", () => {
    expect(espacesNormaux(formater(62897, "entier"))).toBe("62 897");
    expect(espacesNormaux(formater(11.72, "euros"))).toBe("11,72 €");
    expect(espacesNormaux(formater(1.62, "jours"))).toBe("1,6 j");
  });

  it("conserve 0 comme une vraie valeur", () => {
    expect(espacesNormaux(formater(0, "pct"))).toBe("0,0 %");
  });
});