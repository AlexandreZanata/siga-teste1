import br.gov.jfrj.siga.base.DateUtils;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.TimeZone;

/**
 * Aceite isolado de SIGA-REAL-13 ("Data-hora com ano de 4 digitos").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0. Timezone fixado pelo harness.
 */
public class AtlasAccept13 {
  static int passed = 0;
  static int failed = 0;
  static final TimeZone TZ = TimeZone.getTimeZone("America/Sao_Paulo");

  interface Probe {
    Object run() throws Throwable;
  }

  static Date dt(int y, int mo, int d, int h, int mi, int s) {
    Calendar c = new GregorianCalendar(TZ);
    c.set(y, mo, d, h, mi, s);
    c.set(Calendar.MILLISECOND, 0);
    return c.getTime();
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
    TimeZone.setDefault(TZ);
    final Date d1 = dt(2025, 3, 30, 10, 0, 0);
    final Date d2 = dt(2024, 1, 29, 23, 59, 59);
    final Date d3 = dt(2000, 0, 1, 0, 0, 0);

    // O nome promete YYYY: ano com 4 digitos.
    check("full-year", "30/04/2025 10:00:00", () -> DateUtils.formatarDDMMYYYYHHMMSS(d1));
    check("leap-second", "29/02/2024 23:59:59", () -> DateUtils.formatarDDMMYYYYHHMMSS(d2));
    check("y2k", "01/01/2000 00:00:00", () -> DateUtils.formatarDDMMYYYYHHMMSS(d3));
    // Nulo preservado.
    check("null", null, () -> DateUtils.formatarDDMMYYYYHHMMSS(null));
    // Irmaos com ano curto no nome preservados.
    check("ddmmyyyy", "30/04/2025", () -> DateUtils.formatarDDMMYYYY(d1));
    check("ddmmyy", "30/04/25", () -> DateUtils.formatarDDMMYY(d1));

    System.out.println("AtlasAccept13: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
