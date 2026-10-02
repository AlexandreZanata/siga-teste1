import br.gov.jfrj.siga.base.util.Texto;

/**
 * Aceite isolado de SIGA-REAL-01 ("Extrair trecho com delimitador anterior ao inicio").
 *
 * <p>Compila com {@code javac} contra as fontes originais, sem Maven, sem JUnit, sem rede.
 * Cada caso imprime {@code PASS} ou {@code FAIL}; qualquer falha (inclusive excecao nao
 * capturada pelo caso) devolve codigo diferente de zero. Excecao lancada pelo caso e
 * registrada como FAIL com a classe da excecao, nunca como crash sem diagnostico.
 */
public class AtlasAccept01 {
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
    // Criterio 1: fechamento anterior nao causa excecao nem determina o resultado.
    check("close-before-open", "interno",
        () -> Texto.extrai("]ruido[interno]", "[", "]"));
    // Criterio 2: apenas fechamento anterior, abertura ausente e fechamento posterior
    // ausente retornam null.
    check("close-only", null, () -> Texto.extrai("fecha] sem abrir", "[", "]"));
    check("no-delimiters", null, () -> Texto.extrai("texto sem marcas", "[", "]"));
    check("open-without-later-close", null, () -> Texto.extrai("[aberto sem fechar", "[", "]"));
    // Criterio 3: delimitadores adjacentes retornam string vazia; caso simples preservado.
    check("adjacent-delimiters", "", () -> Texto.extrai("[]", "[", "]"));
    check("simple-case", "interno", () -> Texto.extrai("[interno]", "[", "]"));

    System.out.println("AtlasAccept01: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
