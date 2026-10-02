import br.gov.jfrj.siga.base.util.Utils;

/**
 * Aceite isolado de SIGA-REAL-12 ("Zip de configuracao com contrato de vazio").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept12 {
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

  static void checkThrows(String name, Class<?> type, String message, Probe probe) {
    try {
      Object actual = probe.run();
      failed++;
      System.out.println("FAIL " + name + " expected-throw=<" + type.getName() + "> actual=<" + actual + ">");
    } catch (Throwable t) {
      if (type.isInstance(t) && (message == null || message.equals(t.getMessage()))) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " expected-throw=<" + type.getName() + ":" + message + "> threw="
            + t.getClass().getName() + ": " + t.getMessage());
      }
    }
  }

  public static void main(String[] args) {
    // Nulo e vazio rejeitados com IAE claro, nunca NPE.
    checkThrows("enc-null", IllegalArgumentException.class,
        "Conteudo para codificacao nulo ou vazio", () -> Utils.encodeAndZip(null));
    checkThrows("enc-empty", IllegalArgumentException.class,
        "Conteudo para codificacao nulo ou vazio", () -> Utils.encodeAndZip(""));
    checkThrows("dec-null", IllegalArgumentException.class,
        "Conteudo para decodificacao nulo ou vazio", () -> Utils.unzipAndDecode(null));
    checkThrows("dec-empty", IllegalArgumentException.class,
        "Conteudo para decodificacao nulo ou vazio", () -> Utils.unzipAndDecode(""));
    // Round-trip preserva conteudo, inclusive multibyte e longo.
    check("roundtrip", "oi", () -> Utils.unzipAndDecode(Utils.encodeAndZip("oi")));
    check("roundtrip-utf8", "caf\u00e9 \u65e5\u672c\u8a9e",
        () -> Utils.unzipAndDecode(Utils.encodeAndZip("caf\u00e9 \u65e5\u672c\u8a9e")));
    StringBuilder big = new StringBuilder();
    for (int i = 0; i < 5000; i++) {
      big.append('x');
    }
    final String huge = big.toString();
    check("roundtrip-big", huge, () -> Utils.unzipAndDecode(Utils.encodeAndZip(huge)));
    // Base64 invalido continua IAE do decodificador.
    checkThrows("garbage", IllegalArgumentException.class, null, () -> Utils.unzipAndDecode("!!!"));

    System.out.println("AtlasAccept12: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
