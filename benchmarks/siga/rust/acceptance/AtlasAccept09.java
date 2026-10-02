import br.gov.jfrj.siga.base.util.Utils;
import java.util.HashMap;
import java.util.Map;

/**
 * Aceite isolado de SIGA-REAL-09 ("Formulario url-encoded sem perda de dados").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept09 {
  static int passed = 0;
  static int failed = 0;

  interface Probe {
    Object run() throws Throwable;
  }

  static Map<String, String> form(String s) {
    Map<String, String> m = new HashMap<String, String>();
    try {
      Utils.mapFromUrlEncodedForm(m, s.getBytes("ISO-8859-1"));
    } catch (Throwable t) {
      throw new RuntimeException(t);
    }
    return m;
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
    // Pares simples preservados.
    check("simple", "{a=1, b=2}", () -> form("a=1&b=2").toString());
    // Sinal de igual dentro do valor preservado.
    check("equals-in-value", "{a=b=c}", () -> form("a=b=c").toString());
    check("leading-equals", "{x==y}", () -> form("x==y").toString());
    // Valor vazio preservado como string vazia.
    check("empty-value", "{vazio=}", () -> form("vazio=").toString());
    // Par sem '=' continua ignorado.
    check("bare-ignored", "{}", () -> form("flag").toString());
    // Chave repetida: ultimo valor vence.
    check("last-wins", "{a=2}", () -> form("a=1&a=2").toString());
    // '+' decodifica como espaco.
    check("plus-space", "{k=a b}", () -> form("k=a+b").toString());
    // Percent-decoding + unescape HTML preservados.
    check("escapes", "{e=a&b}", () -> form("e=a%26amp%3Bb").toString());
    // Formulario nulo nao toca o mapa.
    check("null-form", "{x=1}", () -> {
      Map<String, String> m = new HashMap<String, String>();
      m.put("x", "1");
      Utils.mapFromUrlEncodedForm(m, null);
      return m.toString();
    });

    System.out.println("AtlasAccept09: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
