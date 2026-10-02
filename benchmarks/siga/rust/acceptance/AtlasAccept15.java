import br.gov.jfrj.siga.base.FormataTamanhoDeArquivo;
import java.util.Locale;

/**
 * Aceite isolado de SIGA-REAL-15 ("Tamanho de arquivo independente de locale").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0. Locale do processo fixado pelo harness.
 */
public class AtlasAccept15 {
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

  static void checkThrows(String name, Class<?> type, Probe probe) {
    try {
      Object actual = probe.run();
      failed++;
      System.out.println("FAIL " + name + " expected-throw=<" + type.getName() + "> actual=<" + actual + ">");
    } catch (Throwable t) {
      if (type.isInstance(t)) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " expected-throw=<" + type.getName() + "> threw="
            + t.getClass().getName() + ": " + t.getMessage());
      }
    }
  }

  public static void main(String[] args) {
    Locale.setDefault(new Locale("pt", "BR"));

    // Separador decimal com ponto em qualquer locale.
    check("bytes", "1.0 bytes", () -> FormataTamanhoDeArquivo.converterEmTexto(1));
    check("bytes-max", "1023.0 bytes", () -> FormataTamanhoDeArquivo.converterEmTexto(1023));
    check("kb", "1.0 kB", () -> FormataTamanhoDeArquivo.converterEmTexto(1024));
    check("kb-frac", "1.5 kB", () -> FormataTamanhoDeArquivo.converterEmTexto(1536));
    check("mb", "1.0 MB", () -> FormataTamanhoDeArquivo.converterEmTexto(1048576));
    check("gb", "1.0 GB", () -> FormataTamanhoDeArquivo.converterEmTexto(1073741824L));
    // Zero e negativos continuam invalidos.
    checkThrows("zero", IllegalArgumentException.class,
        () -> FormataTamanhoDeArquivo.converterEmTexto(0));
    checkThrows("neg", IllegalArgumentException.class,
        () -> FormataTamanhoDeArquivo.converterEmTexto(-5));

    System.out.println("AtlasAccept15: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
