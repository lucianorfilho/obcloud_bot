import time
import logging
from colorama import Fore, init
from config import CONFIG

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class ExnovaBot:
    def __init__(self, test_mode=True):
        self.driver     = None
        self.wait       = None
        self.logged_in  = False
        self.test_mode  = test_mode

    # ------------------------------------------------------------------ #
    # Driver                                                               #
    # ------------------------------------------------------------------ #

    def start_driver(self):
        if self.test_mode:
            logger.info(f"{Fore.YELLOW}🧪 MODO TESTE — Browser não será aberto.")
            return True

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            options = Options()

            # Headless — obrigatório em servidor
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # User agent realista
            options.add_argument(
                "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

            # Caminho fixo do Chromium no Linux (instalado via apt)
            options.binary_location = "/usr/bin/chromium"

            service = Service(executable_path="/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait   = WebDriverWait(self.driver, 20)

            # Remove flag de webdriver via JS
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )

            logger.info(f"{Fore.GREEN}✅ Browser headless iniciado com sucesso.")
            return True

        except Exception as e:
            logger.error(f"{Fore.RED}❌ Erro ao iniciar browser: {e}", exc_info=True)
            self.driver = None
            return False

    def _driver_ok(self):
        try:
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Login                                                                #
    # ------------------------------------------------------------------ #

    def login(self):
        if self.test_mode:
            logger.info(f"{Fore.YELLOW}🧪 MODO TESTE — Login simulado.")
            self.logged_in = True
            return True

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        try:
            logger.info(f"{Fore.YELLOW}🔐 Navegando para login na Exnova...")
            self.driver.get(CONFIG["base_url"])
            time.sleep(4)

            # Email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(CONFIG["email"])
            time.sleep(0.5)

            # Senha
            password_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(CONFIG["password"])
            time.sleep(0.5)

            # Botão submit
            login_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='submit']")
                )
            )
            login_btn.click()

            logger.info(f"{Fore.YELLOW}⏳ Aguardando redirecionamento...")
            time.sleep(7)

            current_url = self.driver.current_url
            logger.info(f"🔗 URL após login: {current_url}")

            if "trade" in current_url or "cabinet" in current_url:
                self.logged_in = True
                logger.info(f"{Fore.GREEN}✅ Login realizado com sucesso!")
                return True

            # Verifica se tem mensagem de erro na página
            try:
                error_el = self.driver.find_element(
                    By.XPATH,
                    "//*[contains(@class,'error') or contains(@class,'alert')]"
                )
                logger.error(f"{Fore.RED}❌ Erro na página: {error_el.text}")
            except Exception:
                pass

            logger.error(f"{Fore.RED}❌ Login falhou. URL atual: {current_url}")
            return False

        except Exception as e:
            logger.error(f"{Fore.RED}❌ Erro no login: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------ #
    # Selecionar par (Normal e OTC)                                        #
    # ------------------------------------------------------------------ #

    def select_pair(self, pair: str, is_otc: bool = False):
        if self.test_mode:
            tipo = "OTC" if is_otc else "Normal"
            logger.info(f"{Fore.CYAN}🧪 Par simulado: {pair} ({tipo})")
            return True

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        pair_name = f"{pair}-OTC" if is_otc else pair

        try:
            if "trade" not in self.driver.current_url:
                self.driver.get(CONFIG["trade_url"])
                time.sleep(3)

            # Abre seletor de ativo
            asset_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//*[contains(@class,'current-symbol') or "
                     "contains(@class,'asset-select') or "
                     "contains(@class,'selected-instrument') or "
                     "contains(@class,'pair-select')]")
                )
            )
            asset_btn.click()
            time.sleep(1)

            # Campo de busca
            search = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='text' or @type='search' or @placeholder]")
                )
            )
            search.clear()
            search.send_keys(pair_name)
            time.sleep(1.5)

            # Clica no resultado
            result = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//*[contains(text(),'{pair_name}')]")
                )
            )
            result.click()
            time.sleep(1)

            logger.info(f"{Fore.CYAN}📊 Par selecionado: {pair_name}")
            return True

        except Exception as e:
            logger.error(
                f"{Fore.RED}❌ Erro ao selecionar par {pair_name}: {e}",
                exc_info=True
            )
            return False

    # ------------------------------------------------------------------ #
    # Expiração                                                            #
    # ------------------------------------------------------------------ #

    def set_expiration(self, minutes: int):
        if self.test_mode:
            logger.info(f"{Fore.CYAN}🧪 Expiração simulada: {minutes}min")
            return True

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        try:
            exp_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//*[contains(@class,'expiration') or "
                     "contains(@class,'duration') or "
                     "contains(@class,'time-picker')]")
                )
            )
            exp_btn.click()
            time.sleep(1)

            option = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     f"//*[contains(text(),'{minutes} min') or "
                     f"contains(text(),'{minutes}m') or "
                     f"text()='{minutes}']")
                )
            )
            option.click()
            time.sleep(0.5)

            logger.info(f"{Fore.CYAN}⏱️ Expiração definida: {minutes}min")
            return True

        except Exception as e:
            logger.error(
                f"{Fore.RED}❌ Erro ao definir expiração: {e}",
                exc_info=True
            )
            return False

    # ------------------------------------------------------------------ #
    # Valor                                                                #
    # ------------------------------------------------------------------ #

    def set_amount(self, amount: float):
        if self.test_mode:
            logger.info(f"{Fore.CYAN}🧪 Valor simulado: ${amount}")
            return True

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        try:
            amount_field = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//input[contains(@class,'amount') or "
                     "contains(@class,'invest') or "
                     "contains(@id,'amount') or "
                     "contains(@name,'amount')]")
                )
            )
            amount_field.clear()
            time.sleep(0.3)
            amount_field.send_keys(str(amount))
            time.sleep(0.5)

            logger.info(f"{Fore.CYAN}💰 Valor definido: ${amount}")
            return True

        except Exception as e:
            logger.error(
                f"{Fore.RED}❌ Erro ao definir valor: {e}",
                exc_info=True
            )
            return False

    # ------------------------------------------------------------------ #
    # Executar trade                                                        #
    # ------------------------------------------------------------------ #

    def execute_trade(self, direction: str):
        if self.test_mode:
            icon  = "📈" if direction == "call" else "📉"
            label = "CALL (Compra)" if direction == "call" else "PUT (Venda)"
            logger.info(f"{Fore.GREEN}🧪 Operação simulada: {icon} {label}")
            return True

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        try:
            if direction.lower() == "call":
                xpath = (
                    "//button[contains(@class,'call') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CALL') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'UP') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ACIMA')]"
                )
                logger.info(f"{Fore.GREEN}📈 Executando CALL...")
            else:
                xpath = (
                    "//button[contains(@class,'put') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PUT') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'DOWN') or "
                    "contains(translate(text(),'abcdefghijklmnopqrstuvwxyz',"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ABAIXO')]"
                )
                logger.info(f"{Fore.RED}📉 Executando PUT...")

            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            btn.click()
            time.sleep(1)

            logger.info(f"{Fore.GREEN}✅ Operação executada com sucesso!")
            return True

        except Exception as e:
            logger.error(
                f"{Fore.RED}❌ Erro ao executar operação: {e}",
                exc_info=True
            )
            return False

    # ------------------------------------------------------------------ #
    # Executar sinal completo                                              #
    # ------------------------------------------------------------------ #

    def execute_signal(self, signal: dict):
        logger.info(f"{Fore.YELLOW}🚀 Executando sinal: {signal}")
        amount = signal.get("amount", CONFIG["default_amount"])
        is_otc = signal.get("market", "normal") == "otc"

        if not self.logged_in or not self._driver_ok():
            self.logged_in = False
            if not self.login():
                return False

        success = (
            self.select_pair(signal["pair"], is_otc=is_otc)
            and self.set_expiration(signal["expiration"])
            and self.set_amount(amount)
            and self.execute_trade(signal["direction"])
        )

        label = "✅ Sucesso" if success else "❌ Falha"
        mkt   = "OTC" if is_otc else "Normal"
        logger.info(
            f"{label} — {signal['pair']} ({mkt}) | "
            f"{signal['direction'].upper()} | {signal['expiration']}min | ${amount}"
        )
        return success

    # ------------------------------------------------------------------ #
    # Fechar                                                               #
    # ------------------------------------------------------------------ #

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            logger.info("🔒 Browser fechado.")