import br.gov.jfrj.siga.base.AcaoVO;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;

/**
 * Aceite isolado de SIGA-REAL-17 ("URL canonica da acao").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 *
 * Contrato: parametros na ordem de iteracao do mapa, sem '&' sobrando,
 * '?' so quando ha parametros, url explicita preservada.
 */
public class AtlasAccept17 {
  static int passed = 0;
  static int failed = 0;

  interface Probe {
    Object run() throws Throwable;
  }

  static AcaoVO acao(String ns, Map<String, String> params) {
    return new AcaoVO("i", "X", ns, "act", true, null,
        new TreeMap<String, String>(params), "pre", "pos", "cls", null);
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
    // Ordem do mapa preservada (TreeMap: a antes de b).
    Map<String, String> dois = new TreeMap<String, String>();
    dois.put("a", "1");
    dois.put("b", "2");
    check("treemap-order", "ns/act?a=1&b=2", () -> acao("ns", dois).getUrl());
    // Ordem de insercao preservada (LinkedHashMap nao ordenado).
    final Map<String, String> linked = new LinkedHashMap<String, String>();
    linked.put("z", "1");
    linked.put("a", "2");
    linked.put("m", "3");
    check("insertion-order", "ns/act?z=1&a=2&m=3", () -> {
      AcaoVO a = new AcaoVO("i", "X", "ns", "act", true, null,
          new TreeMap<String, String>(), "pre", "pos", "cls", null);
      a.setParams(linked);
      return a.getUrl();
    });
    // Parametro unico sem '&' sobrando.
    Map<String, String> um = new TreeMap<String, String>();
    um.put("so", "um");
    check("single", "ns/act?so=um", () -> acao("ns", um).getUrl());
    // Valor vazio preservado, sem '&' sobrando.
    Map<String, String> vazio = new TreeMap<String, String>();
    vazio.put("k", "");
    check("empty-value", "ns/act?k=", () -> acao("ns", vazio).getUrl());
    // Sem parametros: sem '?'.
    check("no-params", "ns/act", () -> acao("ns", new TreeMap<String, String>()).getUrl());
    // Parametros nulos: sem '?'.
    check("null-params", "ns/act", () -> {
      AcaoVO a = new AcaoVO("i", "X", "ns", "act", true, null, null,
          "pre", "pos", "cls", null);
      return a.getUrl();
    });
    // Namespace nulo: acao sozinha com query canonica.
    check("null-namespace", "act?so=um", () -> acao(null, um).getUrl());
    // URL explicita continua preservada como esta.
    check("explicit-url", "http://fixa/url?x=1", () -> {
      AcaoVO a = new AcaoVO("i", "X", "ns", "http://fixa/url?x=1", "act", true, null, null,
          new TreeMap<String, String>(), "pre", "pos", "cls", null);
      return a.getUrl();
    });

    System.out.println("AtlasAccept17: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
