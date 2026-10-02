import br.gov.jfrj.siga.base.Prop;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Aceite isolado de SIGA-REAL-04 ("Normalizacao de listas de configuracao").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept04 {
  static int passed = 0;
  static int failed = 0;

  static void useProvider(Map<String, String> m) {
    Prop.setProvider(new Prop.IPropertyProvider() {
      public String getProp(String n) {
        return m.get(n);
      }

      public void addPrivateProperty(String n) {
      }

      public void addRestrictedProperty(String n) {
      }

      public void addPublicProperty(String n) {
      }

      public void addPrivateProperty(String n, String v) {
        m.put(n, v);
      }

      public void addRestrictedProperty(String n, String v) {
        m.put(n, v);
      }

      public void addPublicProperty(String n, String v) {
        m.put(n, v);
      }
    });
  }

  static void check(String name, Object expected, PropProbe probe) {
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

  interface PropProbe {
    Object run() throws Throwable;
  }

  public static void main(String[] args) {
    Map<String, String> m = new HashMap<String, String>();
    m.put("/t.lista", ", a, , b, ");
    m.put("/t.dupla", "a,a");
    m.put("/t.vazia", "");
    m.put("/t.esp", " a ,b ");
    m.put("/t.um", "x");
    useProvider(m);
    try {
      // Criterio 1: trim + descarta vazias.
      check("spaced", Arrays.asList("a", "b"), () -> Prop.getList("/t.lista"));
      // Criterio 2: ordem e duplicatas preservadas.
      check("dup", Arrays.asList("a", "a"), () -> Prop.getList("/t.dupla"));
      // Criterio 3: vazia -> lista vazia; ausente -> null.
      check("empty", Arrays.asList(), () -> Prop.getList("/t.vazia"));
      check("missing", null, () -> Prop.getList("/t.ausente"));
      // Espacos internos de cada entrada.
      check("each-trimmed", Arrays.asList("a", "b"), () -> Prop.getList("/t.esp"));
      check("single", Arrays.asList("x"), () -> Prop.getList("/t.um"));
    } finally {
      Prop.setProvider(null);
    }

    System.out.println("AtlasAccept04: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
