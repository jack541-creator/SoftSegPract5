import random
import string
def generar_otps(self, cantidad: int) -> list:

        if not isinstance(cantidad, int):
            raise TypeError

        if cantidad <= 0: 
            raise ValueError

    
        caracteres = string.ascii_letters + string.digits

    # SET = no permite duplicados
        otps = set()

        while len(otps) < cantidad:

            otp = ''.join(random.choice(caracteres) for _ in range(6))

            otps.add(otp)

        return list(otps)

    def almacenar_otps(self, clave_maestra: str, servicio: str, usuario: str, otps: list) -> None:
        """
        Almacena las OTPs del usuario.
        Reemplaza las anteriores si existían.
        """

    # Validación básica
        if not isinstance(otps, list):
            raise TypeError

    # Guardar OTPs
        # Guardar COPIA independiente
        self._credenciales[servicio][usuario]["otps"] = otps.copy()


    def verificar_otp(self, clave_maestra, servicio, usuario, otp):

        print("ENTRANDO EN verificar_otp")

        if not isinstance(otp, str):
            return False

        if len(otp) != 6:
            return False

        if otp in self._credenciales[servicio][usuario]["otps"]:

            print("ELIMINANDO OTP")

            self._credenciales[servicio][usuario]["otps"].remove(otp)

            return True

        return False
