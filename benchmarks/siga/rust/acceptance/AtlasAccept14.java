import br.gov.jfrj.siga.base.ReaisPorExtenso;
import java.math.BigDecimal;

/**
 * Aceite isolado de SIGA-REAL-14 ("Milhares sem 'um' por extenso").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept14 {
  static int passed = 0;
  static int failed = 0;

  interface Probe {
    Object run() throws Throwable;
  }

  static String extenso(String v) {
    return new ReaisPorExtenso(new BigDecimal(v)).toString();
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
    // Milhares exatos sem "um".
    check("mil", "mil reais", () -> extenso("1000"));
    check("mil-cem", "mil e cem reais", () -> extenso("1100"));
    check("mil-um", "mil e um reais", () -> extenso("1001"));
    check("mil-extenso", "mil e duzentos e trinta e quatro reais e cinquenta e seis centavos",
        () -> extenso("1234.56"));
    // Demais qualificadores preservados.
    check("dois-mil", "dois mil reais", () -> extenso("2000"));
    check("um-real", "um real", () -> extenso("1"));
    check("cem", "cem reais", () -> extenso("100"));
    check("milhao", "um milh\u00e3o de reais", () -> extenso("1000000"));
    check("centavos", "cinco centavos", () -> extenso("0.05"));

    System.out.println("AtlasAccept14: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
