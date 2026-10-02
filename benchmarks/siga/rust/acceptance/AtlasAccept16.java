import br.gov.jfrj.siga.base.util.Texto;
import java.util.Locale;

/**
 * Aceite isolado de SIGA-REAL-16 ("Slug independente de locale").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0. Locale do processo fixado pelo harness.
 */
public class AtlasAccept16 {
  static int passed = 0;
  static int failed = 0;

  interface Probe {
    Object run() throws Throwable;
  }

  static void check(String name, Object expected, Probe probe) {
    try {
      Object actual = probe.run();
      boolean ok = expected == null ? actual == null : expected.equals(actual);
      if (ok) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " expected=<" + expected + "> actual=<" + actual + ">");
      }
    } catch (Throwable t) {
      failed++;
      System.out.println("FAIL " + name + " threw=" + t.getClass().getName() + ": " + t.getMessage());
    }
  }

  public static void main(String[] args) {
    Locale.setDefault(new Locale("tr", "TR"));

    // 'I' sem pingo: minuscula neutra mesmo em locale turco.
    check("tr-icon", "itbi-icon", () -> Texto.slugify("ITBI Icon", true, false));
    check("tr-hot", "sicak", () -> Texto.slugify("SICAK", true, false));
    check("tr-ad", "ilan", () -> Texto.slugify("ILAN", true, false));
    // Comportamento ja suportado preservado.
    check("accent", "sao-paulo", () -> Texto.slugify("S\u00e3o Paulo", true, false));
    check("punct", "ola-mundo", () -> Texto.slugify("Ol\u00e1 Mundo!", true, false));
    check("underscore", "a_b", () -> Texto.slugify("a b", true, true));
    check("no-lower", "ABC", () -> Texto.slugify("ABC", false, false));
    check("null", null, () -> Texto.slugify(null, true, false));
    check("blank", null, () -> Texto.slugify("   ", true, false));

    System.out.println("AtlasAccept16: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
