import br.gov.jfrj.siga.base.util.Utils;

/**
 * Aceite isolado de SIGA-REAL-10 ("Zeros a esquerda com sinal preservado").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept10 {
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
    // Positivos e zero preservados.
    check("pos", "005", () -> Utils.completarComZeros(5, 3));
    check("zero", "00", () -> Utils.completarComZeros(0, 2));
    check("wide", "12345", () -> Utils.completarComZeros(12345, 3));
    check("single", "7", () -> Utils.completarComZeros(7, 1));
    // Negativos mantem o sinal antes dos zeros.
    check("neg", "-005", () -> Utils.completarComZeros(-5, 3));
    check("neg-one", "-01", () -> Utils.completarComZeros(-1, 2));
    check("neg-wide", "-00100", () -> Utils.completarComZeros(-100, 5));
    // Negativo ja largo nao ganha zeros.
    check("neg-exact", "-999", () -> Utils.completarComZeros(-999, 3));

    System.out.println("AtlasAccept10: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
