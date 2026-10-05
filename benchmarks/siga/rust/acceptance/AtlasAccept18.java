import br.gov.jfrj.siga.base.AcaoVO;
import br.gov.jfrj.siga.base.VO;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;

/**
 * Aceite isolado de SIGA-REAL-18 ("ordenacao sem efeito colateral").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 *
 * Contrato: getAcoesOrdenadasPorNome devolve permitidas primeiro e nome
 * alfabetico ignorando '_' (cadeia VO -> AcaoVO.ordena), SEM reordenar a
 * lista interna do VO. Segunda chamada repete o mesmo resultado.
 */
public class AtlasAccept18 {
  static int passed = 0;
  static int failed = 0;

  static AcaoVO acao(String nome, boolean pode) {
    return new AcaoVO("i", nome, "ns", "act", pode, null,
        new TreeMap<String, String>(), "pre", "pos", "cls", null);
  }

  static List<String> nomes(List<AcaoVO> acoes) {
    List<String> out = new ArrayList<String>();
    for (AcaoVO a : acoes) {
      out.add(a.getNome());
    }
    return out;
  }

  static void check(String name, Object expected, Object actual) {
    boolean ok = expected == null ? actual == null : expected.equals(actual);
    if (ok) {
      passed++;
      System.out.println("PASS " + name);
    } else {
      failed++;
      System.out.println("FAIL " + name + " expected=<" + expected + "> actual=<" + actual + ">");
    }
  }

  public static void main(String[] args) {
    VO vo = new VO();
    vo.addAcao(acao("zebra", true));
    vo.addAcao(acao("abacaxi", true));
    vo.addAcao(acao("morango", false));

    // Ordem contratada: permitidas primeiro, alfabetica entre elas.
    check("ordered-names", "[abacaxi, zebra, morango]", nomes(vo.getAcoesOrdenadasPorNome()).toString());
    // A lista interna mantem a ordem de insercao depois da consulta.
    check("internal-intact", "[zebra, abacaxi, morango]", nomes(vo.getAcoes()).toString());
    // Segunda chamada repete o mesmo resultado ordenado.
    check("stable-repeat", "[abacaxi, zebra, morango]", nomes(vo.getAcoesOrdenadasPorNome()).toString());
    // E a interna segue intacta depois da repeticao.
    check("internal-intact-2", "[zebra, abacaxi, morango]", nomes(vo.getAcoes()).toString());

    // '_' ignorado na comparacao; empate mantem insercao (sort estavel).
    VO vo2 = new VO();
    vo2.addAcao(acao("al_pha", true));
    vo2.addAcao(acao("alpha", true));
    check("underscore-tie", "[al_pha, alpha]", nomes(vo2.getAcoesOrdenadasPorNome()).toString());
    check("underscore-internal", "[al_pha, alpha]", nomes(vo2.getAcoes()).toString());

    // So negadas: alfabetica, sem tocar na interna.
    VO vo3 = new VO();
    vo3.addAcao(acao("zulu", false));
    vo3.addAcao(acao("alfa", false));
    check("denied-ordered", "[alfa, zulu]", nomes(vo3.getAcoesOrdenadasPorNome()).toString());
    check("denied-internal", "[zulu, alfa]", nomes(vo3.getAcoes()).toString());

    // VO vazio: lista vazia, sem excecao.
    check("empty", "[]", nomes(new VO().getAcoesOrdenadasPorNome()).toString());

    System.out.println("AtlasAccept18: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
