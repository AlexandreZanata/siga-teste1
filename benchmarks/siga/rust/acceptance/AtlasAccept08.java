import br.gov.jfrj.siga.base.Prop;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * Aceite isolado de SIGA-REAL-08 ("Datas de configuracao com parsing estrito").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept08 {
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

  interface Probe {
    Object run() throws Throwable;
  }

  static String fmt(Date d) {
    SimpleDateFormat f = new SimpleDateFormat("dd/MM/yyyy");
    f.setLenient(false);
    return f.format(d);
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

  static void checkThrowsData(String name, Probe probe) {
    try {
      Object actual = probe.run();
      failed++;
      String shown = actual instanceof Date ? fmt((Date) actual) : String.valueOf(actual);
      System.out.println("FAIL " + name + " expected-throw=<RuntimeException: Erro ao converter> actual=<" + shown + ">");
    } catch (RuntimeException t) {
      if ("Erro ao converter propriedade string em data".equals(t.getMessage())) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " wrong-message=<" + t.getMessage() + ">");
      }
    } catch (Throwable t) {
      failed++;
      System.out.println("FAIL " + name + " wrong-type=" + t.getClass().getName() + ": " + t.getMessage());
    }
  }

  public static void main(String[] args) {
    Map<String, String> m = new HashMap<String, String>();
    m.put("/t.ok-leap", "29/02/2024");
    m.put("/t.max", "31/12/2099");
    m.put("/t.inexistente-31", "31/02/2025");
    m.put("/t.inexistente-29", "29/02/2025");
    m.put("/t.sufixo", "29/02/2024-tarefa");
    m.put("/t.ano-curto", "01/01/25");
    m.put("/t.branco", " ");
    m.put("/t.formato", "2024-02-29");
    useProvider(m);
    try {
      // Datas reais em dd/MM/yyyy sao aceitas, inclusive bissexto e o default.
      check("leap", "29/02/2024", () -> fmt(Prop.getData("/t.ok-leap")));
      check("max", "31/12/2099", () -> fmt(Prop.getData("/t.max")));
      // Ausencia conserva o default 31/12/2099.
      check("missing", "31/12/2099", () -> fmt(Prop.getData("/t.ausente")));
      // Datas inexistentes, sufixo, ano curto, branco e formato trocado rejeitados.
      checkThrowsData("inexistente-31", () -> Prop.getData("/t.inexistente-31"));
      checkThrowsData("inexistente-29", () -> Prop.getData("/t.inexistente-29"));
      checkThrowsData("sufixo", () -> Prop.getData("/t.sufixo"));
      checkThrowsData("ano-curto", () -> Prop.getData("/t.ano-curto"));
      checkThrowsData("branco", () -> Prop.getData("/t.branco"));
      checkThrowsData("formato", () -> Prop.getData("/t.formato"));
    } finally {
      Prop.setProvider(null);
    }

    System.out.println("AtlasAccept08: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
