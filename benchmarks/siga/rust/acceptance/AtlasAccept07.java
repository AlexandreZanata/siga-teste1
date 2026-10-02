import br.gov.jfrj.siga.ex.util.DocumentoUtil;

/**
 * Aceite isolado de SIGA-REAL-07 ("Codigos de via alem de Z").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept07 {
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

  static void checkThrows(String name, Class<?> expectedType, Probe probe) {
    try {
      Object actual = probe.run();
      failed++;
      System.out.println("FAIL " + name + " expected-throw=<" + expectedType.getName() + "> actual=<" + actual + ">");
    } catch (Throwable t) {
      if (expectedType.isInstance(t)) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " expected-throw=<" + expectedType.getName() + "> threw="
            + t.getClass().getName() + ": " + t.getMessage());
      }
    }
  }

  public static void main(String[] args) {
    // Faixa ja suportada (regressao).
    check("c01", "A", () -> DocumentoUtil.obterLetraViaPorCodigo(1));
    check("c26", "Z", () -> DocumentoUtil.obterLetraViaPorCodigo(26));
    // Extensao sequencial A..Z, AA..AZ, BA...
    check("c27", "AA", () -> DocumentoUtil.obterLetraViaPorCodigo(27));
    check("c28", "AB", () -> DocumentoUtil.obterLetraViaPorCodigo(28));
    check("c52", "AZ", () -> DocumentoUtil.obterLetraViaPorCodigo(52));
    check("c53", "BA", () -> DocumentoUtil.obterLetraViaPorCodigo(53));
    check("c703", "AAA", () -> DocumentoUtil.obterLetraViaPorCodigo(703));
    // Overloads int e String concordam.
    check("str27", "AA", () -> DocumentoUtil.obterLetraViaPorCodigo("27"));
    check("agree-53", DocumentoUtil.obterLetraViaPorCodigo(53),
        () -> DocumentoUtil.obterLetraViaPorCodigo("53"));
    // Valores menores que 1 sao invalidos.
    checkThrows("zero-iae", IllegalArgumentException.class, () -> DocumentoUtil.obterLetraViaPorCodigo(0));
    checkThrows("neg-iae", IllegalArgumentException.class, () -> DocumentoUtil.obterLetraViaPorCodigo(-3));
    // Parsing invalido de String conserva NumberFormatException.
    checkThrows("invalid-nfe", NumberFormatException.class,
        () -> DocumentoUtil.obterLetraViaPorCodigo("x"));

    System.out.println("AtlasAccept07: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
