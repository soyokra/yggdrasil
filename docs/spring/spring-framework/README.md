## 简述
IOC
  - 容器
  - bean的生命周期
  - 循环依赖
AOP

## 目录


## 源码分析目录
- [Application.run](src/Application.run.md)
  - [Application.createApplicationContext](src/Application.createApplicationContext.md)
  - [Application.refreshContext](src/Application.refreshContext.md)
    - [AbstractApplicationContext.prepareRefresh](src/AbstractApplicationContext.prepareRefresh.md)
    - [AbstractApplicationContext.obtainFreshBeanFactory](src/AbstractApplicationContext.obtainFreshBeanFactory.md)
    - [AbstractApplicationContext.prepareBeanFactory](src/AbstractApplicationContext.prepareBeanFactory.md)
    - [AbstractApplicationContext.postProcessBeanFactory](src/AbstractApplicationContext.postProcessBeanFactory.md)
    - [AbstractApplicationContext.invokeBeanFactoryPostProcessors](src/AbstractApplicationContext.invokeBeanFactoryPostProcessors.md)
      - [ConfigurationClassPostProcessor.processConfigBeanDefinitions](src/ConfigurationClassPostProcessor.processConfigBeanDefinitions.md)
        - [ConfigurationClassParser.parse](src/ConfigurationClassParser.parse.md)
          - [AutoConfigurationImportSelector.getAutoConfigurationEntry](src/AutoConfigurationImportSelector.getAutoConfigurationEntry.md)
      - [MapperScannerConfigurer.postProcessBeanDefinitionRegistry](src/MapperScannerConfigurer.postProcessBeanDefinitionRegistry.md)
        - [ClassPathMapperScanner.scan](src/ClassPathMapperScanner.scan.md)
    - [AbstractApplicationContext.registerBeanPostProcessors](src/AbstractApplicationContext.registerBeanPostProcessors.md)
    - [AbstractApplicationContext.initMessageSource](src/AbstractApplicationContext.initMessageSource.md)
    - [AbstractApplicationContext.initApplicationEventMulticaster](src/AbstractApplicationContext.initApplicationEventMulticaster.md)
    - [AbstractApplicationContext.onRefresh](src/AbstractApplicationContext.onRefresh.md)
      - [ServletWebServerApplicationContext.onRefresh](src/ServletWebServerApplicationContext.onRefresh.md)
    - [AbstractApplicationContext.registerListeners](src/AbstractApplicationContext.registerListeners.md)
    - [AbstractApplicationContext.finishBeanFactoryInitialization](src/AbstractApplicationContext.finishBeanFactoryInitialization.md)
    - [AbstractApplicationContext.finishRefresh](src/AbstractApplicationContext.finishRefresh.md)
    - [AbstractApplicationContext.destroyBeans](src/AbstractApplicationContext.destroyBeans.md)
    - [AbstractApplicationContext.cancelRefresh](src/AbstractApplicationContext.cancelRefresh.md)
    - [AbstractApplicationContext.resetCommonCaches](src/AbstractApplicationContext.resetCommonCaches.md)


  
- 总的流程图
- 注册BeanDefinition流程图
- 注册Bean流程图
- 本地话消息流程图
- 事件监听，注册，广播流程图