import br.gov.jfrj.siga.base.DateUtils;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.TimeZone;

/**
 * Aceite isolado de SIGA-REAL-11 ("Duracao entre datas sem sinal trocado").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0. Timezone fixado pelo harness.
 */
public class AtlasAccept11 {
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
    final Date ini = dt(2025, 3, 30, 10, 0, 0);
    final Date fim2h = dt(2025, 3, 30, 12, 30, 0);
    final Date fim45m = dt(2025, 3, 30, 10, 45, 0);
    final Date fim45s = dt(2025, 3, 30, 10, 0, 45);
    final Date dia1 = dt(2025, 4, 1, 10, 0, 0);
    final Date dia7 = dt(2025, 4, 7, 10, 0, 0);

    // Mesmo dia em ordem natural: delega horas/minutos/segundos.
    check("same-day-hours", "2h", () -> DateUtils.intervalo(ini, fim2h));
    check("same-day-min", "45min", () -> DateUtils.intervalo(ini, fim45m));
    check("same-day-sec", "45s", () -> DateUtils.intervalo(ini, fim45s));
    // Ordem invertida mede a mesma duracao, nunca negativa.
    check("reversed-hours", "2h", () -> DateUtils.intervalo(fim2h, ini));
    check("reversed-days", "7 dias", () -> DateUtils.intervalo(dia7, ini));
    // Dias com singular correto.
    check("one-day", "1 dia", () -> DateUtils.intervalo(ini, dia1));
    check("one-day-rev", "1 dia", () -> DateUtils.intervalo(dia1, ini));
    // Varios dias em ordem natural.
    check("week", "7 dias", () -> DateUtils.intervalo(ini, dia7));

    System.out.println("AtlasAccept11: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
