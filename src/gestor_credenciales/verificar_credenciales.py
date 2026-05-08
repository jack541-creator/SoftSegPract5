import random
import string


class GestorCredenciales:

    def generar_otps(self, cantidad: int) -> list:
        """
        Genera una lista de OTPs aleatorias.
        """

        # Validación básica
        if not isinstance(cantidad, int):
            raise TypeError("La cantidad debe ser un entero")

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        # Lista de OTPs
        otps = []

        # Caracteres permitidos
        caracteres = string.ascii_letters + string.digits

        # Generación de OTPs
        for _ in range(cantidad):

            # OTP de 6 caracteres
            otp = ''.join(random.choice(caracteres) for _ in range(6))

            otps.append(otp)

        return otps


    def almacenar_otps(self, clave_maestra: str, servicio: str, usuario: str, otps: list) -> None:
        """
        Almacena las OTPs del usuario.
        Reemplaza las OTPs anteriores.
        """

        self._credenciales[servicio][usuario]["otps"] = otps


    def verificar_otp(self, clave_maestra: str, servicio: str, usuario: str, otp: str) -> bool:
        """
        Verifica si una OTP es válida.
        Si es correcta, se elimina para impedir reutilización.
        """

        # OTP debe ser string
        if not isinstance(otp, str):
            return False

        # Debe tener exactamente 6 caracteres
        if len(otp) != 6:
            return False

        # Obtener OTPs almacenadas
        otps = self._credenciales[servicio][usuario].get("otps", [])

        # Verificación
        if otp in otps:

            # Eliminar OTP usada
            otps.remove(otp)

            return True

        return False
