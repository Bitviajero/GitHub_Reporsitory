class CuentaBancaria:
    def __init__(self, saldo_inicial):
        self.__balance = saldo_inicial # balance privado
    def depositar(self, monto):
        self.__balance += monto
    def consultar_balance(self):
        return self.__balance
# Crear una cuenta y realizar operaciones
cuenta = CuentaBancaria(1000)
cuenta.depositar(500)
print(cuenta.consultar_balance()) # Salida: 1500