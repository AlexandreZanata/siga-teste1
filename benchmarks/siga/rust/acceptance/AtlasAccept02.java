import br.gov.jfrj.siga.ex.util.DocumentoUtil;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

/**
 * Aceite isolado de SIGA-REAL-02 ("Localidade com hifen e UF no documento").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept02 {
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
    TimeZone.setDefault(TimeZone.getTimeZone("America/Sao_Paulo"));
    Locale.setDefault(Locale.ENGLISH);
    Date d = new Date(1746057600000L); // 2025-04-30 em Sao_Paulo
    Date d2017 = new Date(1510884000000L);

    // Criterio 1: espacos externos + grafia mista, hifen interno preservado, UF em maiusculas.
    check("spaces-mixed-uf", "Ji-Paraná-RO, 30 de abril de 2025.",
        () -> DocumentoUtil.obterDataExtenso("  jI-pArAnÁ-ro  ", d));
    // Criterio 3: localidade sem UF continua formatada (sem espacos externos).
    check("no-uf-trimmed", "Sao Paulo, 30 de abril de 2025.",
        () -> DocumentoUtil.obterDataExtenso("  Sao Paulo  ", d));
    // Criterio 3: politica de null preservada.
    check("null-localidade", null, () -> DocumentoUtil.obterDataExtenso(null, d));
    // Caso simples preservado.
    check("simple-uf", "Niteroi-RJ, 30 de abril de 2025.",
        () -> DocumentoUtil.obterDataExtenso("Niteroi-RJ", d));
    // Regressao: casos do DocumentoUtilTest legado.
    check("legacy-upper-uf", "Campo dos Goytacazes-RJ, 17 de novembro de 2017.",
        () -> DocumentoUtil.obterDataExtenso("CAMPO DOS GOYTACAZES-RJ", d2017));
    check("legacy-no-uf", "Campo dos Goytacazes, 17 de novembro de 2017.",
        () -> DocumentoUtil.obterDataExtenso("campo dos goyTACAZes", d2017));

    System.out.println("AtlasAccept02: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
